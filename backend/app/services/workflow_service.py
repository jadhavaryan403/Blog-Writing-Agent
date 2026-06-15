"""
app/services/workflow_service.py
──────────────────────────────────
Workflow Service — bridges FastAPI endpoints ↔ LangGraph graph.

Responsibilities:
1. Start a new blog generation workflow (job)
2. Persist WorkflowState snapshots after every step
3. Return current state (including plan) to the API layer
4. Resume workflow after human approval
5. Load user preferences before planning
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.blog import Blog, WorkflowState, UserPreference
from app.langgraph.graph import compiled_graph
from app.langgraph.state import BlogState
from app.schemas import PlanSchema, SectionSchema, WorkflowStatusResponse


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _load_preferences(db: AsyncSession, user_id: int) -> dict[str, Any]:
    result = await db.execute(select(UserPreference).where(UserPreference.user_id == user_id))
    pref = result.scalar_one_or_none()
    if pref is None:
        return {}
    return {
        "preferred_tone": pref.preferred_tone,
        "preferred_style": pref.preferred_style,
        "preferred_word_count": pref.preferred_word_count,
        "preferred_language": pref.preferred_language,
        "technical_depth": pref.technical_depth,
    }


async def _upsert_workflow_state(
    db: AsyncSession,
    blog_id: int,
    job_id: str,
    state: BlogState,
) -> None:
    result = await db.execute(
        select(WorkflowState).where(WorkflowState.job_id == job_id)
    )
    row = result.scalar_one_or_none()

    serialized = {k: v for k, v in state.items() if k not in {"final_blog"}}
    # Store final_blog separately to keep the JSON lean

    if row:
        await db.execute(
            update(WorkflowState)
            .where(WorkflowState.job_id == job_id)
            .values(
                current_node=state.get("current_node"),
                serialized_state=serialized,
                status=state.get("status", "pending"),
            )
        )
    else:
        db.add(WorkflowState(
            blog_id=blog_id,
            job_id=job_id,
            current_node=state.get("current_node"),
            serialized_state=serialized,
            status=state.get("status", "pending"),
        ))
    await db.commit()


# ── Public API ────────────────────────────────────────────────────────────────

async def start_workflow(
    db: AsyncSession,
    user_id: int,
    topic: str,
) -> dict[str, Any]:
    """
    Create Blog record, build initial state, run the graph until the
    first interrupt (after Planner), persist state, return job_id + blog_id.
    """
    # 1. Create Blog row
    blog = Blog(user_id=user_id, topic=topic, status="planning")
    db.add(blog)
    await db.flush()   # get blog.id without committing
    await db.commit()
    await db.refresh(blog)

    job_id = str(uuid.uuid4())

    # 2. Load user preferences
    preferences = await _load_preferences(db, user_id)

    # 3. Build initial state
    now = datetime.now(timezone.utc).isoformat()
    initial_state: BlogState = {
        "job_id": job_id,
        "user_id": user_id,
        "blog_id": blog.id,
        "topic": topic,
        "user_preferences": preferences,
        "status": "planning",
        "current_node": "planner",
        "metrics": {"total_tokens": 0, "total_cost": 0.0, "node_latencies": {}},
        "created_at": now,
        "updated_at": now,
    }

    # 4. Run graph until interrupt (after planner, before human_approval)
    config = {"configurable": {"thread_id": job_id}}
    final_state: BlogState = {}

    async for event in compiled_graph.astream(initial_state, config=config):
        for node_name, node_output in event.items():
            if isinstance(node_output, dict):
                final_state.update(node_output)

    # 5. Persist state snapshot
    await _upsert_workflow_state(db, blog.id, job_id, final_state)

    # 6. Update blog status
    await db.execute(
        update(Blog).where(Blog.id == blog.id).values(status="awaiting_approval")
    )
    await db.commit()

    return {"job_id": job_id, "blog_id": blog.id, "status": "awaiting_approval"}


async def get_workflow_status(
    db: AsyncSession,
    job_id: str,
) -> WorkflowStatusResponse:
    """Return current workflow status + plan (if available)."""
    result = await db.execute(
        select(WorkflowState).where(WorkflowState.job_id == job_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        return WorkflowStatusResponse(
            job_id=job_id,
            blog_id=0,
            status="not_found",
            current_node=None,
            error="Workflow not found",
        )

    state: dict = row.serialized_state or {}
    plan = None
    if state.get("title") and state.get("sections"):
        plan = PlanSchema(
            title=state["title"],
            sections=[SectionSchema(**s) for s in state.get("sections", [])],
            research_required=state.get("research_required", False),
            research_tasks=state.get("research_tasks", {}),
            estimated_word_count=state.get("estimated_word_count", 1500),
        )

    # Fetch final_blog from Blog table if completed
    blog_result = await db.execute(select(Blog).where(Blog.id == row.blog_id))
    blog = blog_result.scalar_one_or_none()
    final_blog = blog.final_content if blog else None

    return WorkflowStatusResponse(
        job_id=job_id,
        blog_id=row.blog_id,
        status=row.status,
        current_node=row.current_node,
        plan=plan,
        final_blog=final_blog,
    )


async def approve_plan(
    db: AsyncSession,
    job_id: str,
    edited_plan: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Resume the workflow after human approval.
    If edited_plan is provided, update the state before resuming.
    """
    result = await db.execute(
        select(WorkflowState).where(WorkflowState.job_id == job_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise ValueError(f"Workflow {job_id} not found")

    config = {"configurable": {"thread_id": job_id}}

    # If user edited the plan, inject the updates into the graph state
    if edited_plan:
        update_data = {
            "title": edited_plan.get("title"),
            "sections": edited_plan.get("sections"),
            "estimated_word_count": edited_plan.get("estimated_word_count"),
            "human_approved": True,
        }
        await compiled_graph.aupdate_state(config, update_data, as_node="human_approval")
    else:
        await compiled_graph.aupdate_state(
            config, {"human_approved": True}, as_node="human_approval"
        )

    # Update DB
    await db.execute(
        update(WorkflowState)
        .where(WorkflowState.job_id == job_id)
        .values(status="running")
    )
    await db.execute(
        update(Blog)
        .where(Blog.id == row.blog_id)
        .values(status="running")
    )
    await db.commit()

    # Resume graph execution in background
    asyncio.create_task(_run_to_completion(db, job_id, row.blog_id, config))

    return {"job_id": job_id, "status": "running", "message": "Workflow resumed"}


async def _run_to_completion(
    db: AsyncSession,
    job_id: str,
    blog_id: int,
    config: dict,
) -> None:
    """Background task: run graph to completion and persist each step."""
    try:
        final_state: BlogState = {}
        async for event in compiled_graph.astream(None, config=config):
            for node_name, node_output in event.items():
                if isinstance(node_output, dict):
                    final_state.update(node_output)
                    # Persist after every node
                    async with db.begin():
                        await _upsert_workflow_state(db, blog_id, job_id, final_state)
    except Exception as exc:
        # Mark as error
        async with db.begin():
            await db.execute(
                update(WorkflowState)
                .where(WorkflowState.job_id == job_id)
                .values(status="error")
            )
            await db.execute(
                update(Blog)
                .where(Blog.id == blog_id)
                .values(status="error")
            )