"""
app/langgraph/agents/image_planner.py
───────────────────────────────────────
Image Planner Agent — analyses the completed blog and generates
targeted image search queries for each section.
"""

from __future__ import annotations

import json
import time

from langchain_core.messages import HumanMessage, SystemMessage

from app.langgraph.llm import get_llm
from app.langgraph.state import BlogState, ImageQueryDict

SYSTEM_PROMPT = """You are an image curation specialist for blog content.
Given blog section titles and descriptions, select the most visual sections and generate image search queries.

Return ONLY a JSON array:

[
{"section_idx": 1, "query": "specific image search query"},
{"section_idx": 4, "query": "..."}
]

Guidelines:

* Select a maximum of 2 images for the entire blog.
* Prefer sections containing comparisons, processes, statistics, diagrams, workflows, concepts, or visual examples.
* Skip Introduction and Conclusion sections.
* Use specific, descriptive search queries (4-8 words).
* Prefer terms like "diagram", "illustration", "infographic", "workflow", or "photo" when appropriate.
* Only select sections where an image adds clear value.
* Return ONLY the JSON array.
  """


async def run_image_planner(state: BlogState) -> dict:
    """LangGraph node: Image Planner."""
    t0 = time.monotonic()
    llm = get_llm(temperature=0.3)
    sections = state.get("sections", [])

    section_summary = "\n".join(
        f"{i}. {s.get('title', '')}\n{s.get('description','')}\n" for i, s in enumerate(sections ,start=1)
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"""Blog title: "{state.get('title', '')}"
            Sections:
            {section_summary}"""),
    ]

    response = await llm.ainvoke(messages)
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()

    queries_raw: list[dict] = json.loads(raw)
    image_queries: list[ImageQueryDict] = [
        ImageQueryDict(section_idx=q["section_idx"], query=q["query"])
        for q in queries_raw
    ]

    latency = time.monotonic() - t0
    usage = response.response_metadata.get("token_usage", {})
    tokens = usage.get("total_tokens", 0)
    metrics = state.get("metrics", {})
    node_latencies = dict(metrics.get("node_latencies", {}))
    node_latencies["image_planner"] = latency
    node_token = dict(metrics.get("node_token", {}))
    node_token["image_planner"] = tokens

    print(state.get("metrics", {}).get("node_latencies", {}))
    print(state.get("metrics", {}).get("node_token", {}))

    return {
        "image_queries": image_queries,
        "status": "image_searching",
        "current_node": "image_search",
        "metrics": {
            **metrics,
            "total_tokens": metrics.get("total_tokens", 0) + tokens,
            "total_cost": metrics.get("total_cost", 0.0) + tokens * 0.25 / 1_000_000,
            "node_latencies": node_latencies,
            "node_token": node_token,
        },
    }