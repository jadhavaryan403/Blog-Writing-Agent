"""
app/langgraph/agents/researcher.py
────────────────────────────────────
Research Agent — uses Tavily for multi-step web research.

For each research_task, performs a Tavily search and collects:
- content snippets
- source URLs + titles (stored as citations)
"""

from __future__ import annotations

import time
from typing import Any

from tavily import TavilyClient

from app.core.config import settings
from app.langgraph.state import BlogState, CitationDict, ResearchResultDict


async def run_researcher(state: BlogState) -> dict:
    """LangGraph node: Research."""
    if not state.get("research_required", False):
        return {"status": "writing", "current_node": "generate"}

    client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    tasks: dict[str, str] = state.get("research_tasks", {})

    all_results: list[ResearchResultDict] = list(state.get("research_results", []))
    all_citations: list[CitationDict] = list(state.get("citations", []))

    t0 = time.monotonic()

    for task_id, task in tasks.items():
        try:
            response = client.search(
                query=task,
                search_depth="advanced",
                max_results=1,
                include_answer=True,
            )

            # Build content summary
            answer = response.get("answer", "")
            results_raw = response.get("results", [])
            snippets = "\n\n".join(
                f"**{r.get('title', '')}**\n{r.get('content', '')}"
                for r in results_raw
            )
            content = f"{answer}\n\n{snippets}".strip()

            sources = [
                {"url": r.get("url", ""), "title": r.get("title", "")}
                for r in results_raw
                if r.get("url")
            ]

            all_results.append(
                ResearchResultDict(task_id=task_id, task=task, content=content, sources=sources)
            )

            # Add citations
            for src in sources:
                all_citations.append(
                    CitationDict(
                        section_idx=-1,   # will be refined during stitching
                        source_url=src["url"],
                        source_title=src["title"],
                    )
                )
        except Exception as exc:
            # Non-fatal: log and continue
            all_results.append(
                ResearchResultDict(task_id=task_id, task=task, content=f"Research failed: {exc}", sources=[])
            )

    latency = time.monotonic() - t0
    metrics = state.get("metrics", {})
    node_latencies = dict(metrics.get("node_latencies", {}))
    node_latencies["researcher"] = latency

    return {
        "research_results": all_results,
        "citations": all_citations,
        "status": "writing",
        "current_node": "generate",
        "metrics": {**metrics, "node_latencies": node_latencies},
    }