"""
app/services/edit_service.py
──────────────────────────────
Section Edit Service
─────────────────────
Orchestrates the section-edit flow:

1. Load the latest WorkflowState for the blog (has sections + research).
2. Run the Section Editor agent on the targeted section.
3. Replace the section draft in-state.
4. Re-run the Stitcher to rebuild the final markdown.
5. Persist the updated blog content + bump a version counter.
6. Return the updated blog markdown + updated section content + version.

Architecture note:
  We re-use _build_final_blog() directly from the stitcher module rather
  than re-running the full LangGraph graph. This keeps edits fast and
  avoids re-triggering research / review / image nodes.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.blog import Blog, WorkflowState, AgentRun, UsageMetric
from app.services.metrics_service import get_usage
from app.langgraph.agents.section_editor import edit_section
from app.langgraph.agents.stitcher import _build_final_blog
from app.langgraph.state import BlogState, SectionDict


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _load_blog_and_state(
    db: AsyncSession, blog_id: int, user_id: int
) -> tuple[Blog, WorkflowState]:
    """Load Blog + most-recent WorkflowState, enforcing ownership."""
    blog_result = await db.execute(
        select(Blog).where(Blog.id == blog_id, Blog.user_id == user_id)
    )
    blog = blog_result.scalar_one_or_none()
    if blog is None:
        raise HTTPException(status_code=404, detail="Blog not found")

    # Get the most recent workflow state for this blog
    ws_result = await db.execute(
        select(WorkflowState)
        .where(WorkflowState.blog_id == blog_id)
        .order_by(WorkflowState.updated_at.desc())
    )
    ws = ws_result.scalars().first()
    if ws is None or not ws.serialized_state:
        raise HTTPException(
            status_code=422,
            detail="Blog workflow state not found. Cannot edit sections.",
        )

    return blog, ws


def _resolve_section_idx(sections: list[SectionDict], section_id: str) -> int:
    """
    Resolve section_id → zero-based index.

    section_id can be:
      - A zero-based integer index as a string  ("0", "1", …)
      - A section title (case-insensitive match)
    """
    # Try integer index first
    try:
        idx = int(section_id)
        if 0 <= idx < len(sections):
            return idx
        raise HTTPException(
            status_code=400,
            detail=f"section_id {idx} out of range (blog has {len(sections)} sections)"
        )
    except ValueError:
        pass

    # Try title match
    lower_id = section_id.strip().lower()
    for i, sec in enumerate(sections):
        if sec.get("title", "").strip().lower() == lower_id:
            return i

    raise HTTPException(
        status_code=400,
        detail=f"Section '{section_id}' not found. "
               f"Available sections: {[s.get('title') for s in sections]}"
    )


# ── Public API ────────────────────────────────────────────────────────────────

async def edit_blog_section(
    db: AsyncSession,
    blog_id: int,
    user_id: int,
    section_id: str,
    instruction: str,
) -> dict:
    """
    Edit a single section of a completed blog.

    Returns:
        {
            "updated_blog":    <full markdown string>,
            "updated_section": <just the edited section markdown>,
            "section_title":   <title of edited section>,
            "section_idx":     <zero-based index>,
            "version":         <incremented integer>,
        }
    """
    # 1. Load blog + workflow state
    blog, ws = await _load_blog_and_state(db, blog_id, user_id)
    state: BlogState = ws.serialized_state  # type: ignore[assignment]

    sections: list[SectionDict] = state.get("sections", [])
    if not sections:
        raise HTTPException(status_code=422, detail="No sections found in blog state.")

    # 2. Resolve section
    section_idx = _resolve_section_idx(sections, section_id)
    section_title = sections[section_idx].get("title", f"Section {section_idx + 1}")

    # 3. Run Section Editor LLM
    updated_draft, usage = await edit_section(
        blog_title=state.get("title", blog.title or ""),
        sections=sections,
        section_idx=section_idx,
        instruction=instruction,
        research_results=state.get("research_results", []),
        citations=state.get("citations", []),
    )

    # 4. Patch the section draft in state (immutable-style)
    updated_sections = [
        {**sec, "draft": updated_draft} if i == section_idx else sec
        for i, sec in enumerate(sections)
    ]
    updated_state: BlogState = {**state, "sections": updated_sections}

    # 5. Re-stitch the full blog
    updated_blog_md = _build_final_blog(updated_state)

    # 6. Compute new version number
    new_version = (blog.edit_version or 1) + 1

    # 7. Persist changes to DB
    # 7a. Update Blog.final_content
    await db.execute(
        update(Blog)
        .where(Blog.id == blog_id)
        .values(
            final_content=updated_blog_md,
            updated_at=datetime.now(timezone.utc),
            edit_version=new_version,
        )
    )

    # 7b. Update WorkflowState.serialized_state
    updated_state["edit_version"] = new_version  # type: ignore[typeddict-unknown-key]
    await db.execute(
        update(WorkflowState)
        .where(WorkflowState.id == ws.id)
        .values(serialized_state=updated_state)
    )

    # 7c. Log agent run
    db.add(AgentRun(
        blog_id=blog_id,
        agent_name="section_editor",
        tokens_used=usage["tokens"],
        cost=usage["cost"],
        latency=usage["latency"],
    ))

    # 7d. Update UsageMetric for the user
    usage_metric = await get_usage(db, user_id)
    if usage_metric:
        usage_metric.total_tokens += usage["tokens"]
        usage_metric.total_cost += usage["cost"]
        usage_metric.last_updated = datetime.now(timezone.utc)
    else:
        db.add(UsageMetric(
            user_id=user_id,
            total_tokens=usage["tokens"],
            total_cost=usage["cost"],
            last_updated=datetime.now(timezone.utc),
        ))

    await db.commit()

    return {
        "updated_blog":    updated_blog_md,
        "updated_section": updated_draft,
        "section_title":   section_title,
        "section_idx":     section_idx,
        "version":         new_version,
    }


async def get_blog_sections(
    db: AsyncSession,
    blog_id: int,
    user_id: int,
) -> list[dict]:
    """
    Return the section list for a blog (title + index + word count).
    Used by the frontend to populate the section picker without exposing
    raw state internals.
    """
    _, ws = await _load_blog_and_state(db, blog_id, user_id)
    state: BlogState = ws.serialized_state  # type: ignore[assignment]
    sections: list[SectionDict] = state.get("sections", [])

    return [
        {
            "section_id":  str(i),          # stable integer index as string
            "title":       sec.get("title", f"Section {i + 1}"),
            "word_count":  sec.get("word_count", 0),
            "has_content": bool(sec.get("draft")),
        }
        for i, sec in enumerate(sections)
    ]