"""
app/langgraph/agents/writer.py
───────────────────────────────
Writer Agent — generates markdown content for each blog section.

Receives the plan sections + research notes and writes them one by one.
Citations are embedded using [Source: URL] notation.
"""

from __future__ import annotations

import asyncio
import time

from langchain_core.messages import HumanMessage, SystemMessage

from app.langgraph.llm import get_llm
from app.langgraph.state import BlogState, SectionDict

SYSTEM_PROMPT = """You are an expert blog writer. Write detailed, engaging, well-structured markdown content for a single blog section.

Requirements:
- Write in the requested tone and style.
- Match the target word count closely.
- Write like a human blogger, not an academic paper.
- Prioritize readability, flow, and engagement.
- Include inline citations only for important statistics, studies, or factual claims: [Source Title](URL)
- Limit citations to 1–2 per section and avoid over-citation.
- Use markdown: headers (##/###), bullet lists, bold, italic where appropriate.
- Do NOT include the section title heading — it will be added automatically.
- Return ONLY the markdown body, no preamble.
"""


def _build_section_prompt(
    title: str,
    description: str,
    word_count: int,
    research_notes: str,
    blog_title: str,
    preferences: dict,
) -> str:
    return f"""Blog title: "{blog_title}"
Section title: "{title}"
Description: {description}
Target word count: {word_count}
Tone: {preferences.get('preferred_tone', 'professional')}
Style: {preferences.get('preferred_style', 'informative')}
Language: {preferences.get('preferred_language', 'English')}
Technical depth: {preferences.get('technical_depth', 'intermediate')}

Research notes:
{research_notes if research_notes else 'No specific research notes for this section. Write from general knowledge.'}

Write the section now."""


def _compile_research_notes(state: BlogState, section_id: str) -> str:
    """Compile only the research results relevant to a single section."""
    results = []
    for r in state.get("research_results", []):
        if r.get("task_id") == section_id:
            results.append(r)

    if not results:
        return ""

    parts = []
    for r in results:
        parts.append(f"### Research: {r['task']}\n{r['content']}")
        for src in r.get("sources", []):
            parts.append(f"- [{src.get('title', 'Source')}]({src.get('url', '')})")
    return "\n\n".join(parts)


async def _write_section(
    section: SectionDict,
    research_notes: str,
    blog_title: str,
    preferences: dict,
    llm,
) -> str:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=_build_section_prompt(
            title=section.get("title", ""),
            description=section.get("description", ""),
            word_count=section.get("word_count", 300),
            research_notes=research_notes,
            blog_title=blog_title,
            preferences=preferences,
        )),
    ]
    response = await llm.ainvoke(messages)
    return response.content.strip(), response.response_metadata.get("token_usage", {})


async def run_writer(state: BlogState) -> dict:
    """LangGraph node: Generate (write all sections concurrently)."""
    t0 = time.monotonic()
    llm = get_llm(temperature=0.7)
    sections: list[SectionDict] = state.get("sections", [])
    blog_title = state.get("title", "")
    preferences = state.get("user_preferences", {})

    # Write all sections concurrently for speed
    tasks = [
        _write_section(
            section,
            _compile_research_notes(state, idx),
            blog_title,
            preferences,
            llm,
        )
        for idx, section in enumerate(sections, start=1)
    ]
    results = await asyncio.gather(*tasks)

    drafts = []
    total_tokens = 0
    for draft, usage in results:
        drafts.append(draft)
        total_tokens += usage.get("total_tokens", 0)

    # Attach drafts back to sections
    updated_sections = []
    for section, draft in zip(sections, drafts):
        updated_sections.append({**section, "draft": draft})

    cost = total_tokens * 0.25 / 1_000_000
    latency = time.monotonic() - t0
    metrics = state.get("metrics", {})
    node_latencies = dict(metrics.get("node_latencies", {}))
    node_latencies["writer"] = latency
    node_token = dict(metrics.get("node_token", {}))
    node_token["writer"] = total_tokens

    print(state.get("metrics", {}).get("node_latencies", {}))
    print(state.get("metrics", {}).get("node_token", {}))

    return {
        "sections": updated_sections,
        "section_drafts": drafts,
        "status": "image_planning",
        "current_node": "image_planner",
        "metrics": {
            **metrics,
            "total_tokens": metrics.get("total_tokens", 0) + total_tokens,
            "total_cost": metrics.get("total_cost", 0.0) + cost,
            "node_latencies": node_latencies,
            "node_token": node_token
        },
    }