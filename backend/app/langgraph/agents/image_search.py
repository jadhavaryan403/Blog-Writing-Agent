"""
app/langgraph/agents/image_search.py
──────────────────────────────────────
Image Search Agent — uses SerpAPI Google Images to fetch
image URLs, titles, sources, and alt text for each planned query.
"""

from __future__ import annotations

import time
from serpapi import GoogleSearch

from app.core.config import settings
from app.langgraph.state import BlogState, ImageResultDict


async def run_image_search(state: BlogState) -> dict:
    """LangGraph node: Image Search."""
    t0 = time.monotonic()

    queries = state.get("image_queries", [])
    image_results: list[ImageResultDict] = []

    for query_item in queries:
        section_idx = query_item.get("section_idx", 0)
        query = query_item.get("query", "")

        try:
            search = GoogleSearch({
                "q": query,
                "tbm": "isch",           # image search
                "num": 2,
                "api_key": settings.SERPAPI_API_KEY,
                "safe": "active",
            })
            results = search.get_dict()
            images_raw = results.get("images_results", [])[:3]  

            for img in images_raw:
                image_results.append(
                    ImageResultDict(
                        section_idx=section_idx,
                        image_url=img.get("original", img.get("thumbnail", "")),
                        title=img.get("title", ""),
                        source=img.get("source", ""),
                        alt_text=img.get("title", query),
                    )
                )
        except Exception as exc:
            # Non-fatal: continue without image for this section
            image_results.append(ImageResultDict(
                section_idx=section_idx,
                image_url="",
                title="",
                source="",
                alt_text=f"Image not available: {exc}",
            ))

    latency = time.monotonic() - t0
    metrics = state.get("metrics", {})
    node_latencies = dict(metrics.get("node_latencies", {}))
    node_latencies["image_search"] = latency

    return {
        "image_results": image_results,
        "status": "stitching",
        "current_node": "stitch_blog",
        "metrics": {**metrics, "node_latencies": node_latencies},
    }