"""
app/langgraph/agents/stitcher.py
──────────────────────────────────
Stitch Blog Agent — combines title, sections, images, and citations
into the final markdown blog post.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from app.langgraph.state import BlogState, CitationDict, ImageResultDict


def _build_final_blog(state: BlogState) -> str:
    title = state.get("title", "Untitled")
    sections = state.get("sections", [])
    images: list[ImageResultDict] = state.get("image_results", [])
    citations: list[CitationDict] = state.get("citations", [])

    # Build section → image map
    img_map: dict[int, List[ImageResultDict]] = {}
    for img in images:
        if img.get("section_idx") is not None:
            img_map.setdefault(img.get("section_idx"), []).append(img)
    
    lines: list[str] = []

    # ── Title ──────────────────────────────────────────────────────────────────
    lines.append(f"# {title}\n")
    lines.append(f"*Generated on {datetime.now(timezone.utc).strftime('%B %d, %Y')}*\n")
    lines.append("---\n")

    # ── Sections ──────────────────────────────────────────────────────────────
    for idx, section in enumerate(sections ,start=1):
        section_title = section.get("title", f"Section {idx}")
        draft = section.get("draft", "")

        lines.append(f"## {section_title}\n")

        # Insert image if available for this section
        import requests

        if idx in img_map:
            for img in img_map[idx]:
                try:
                    url = img.get("image_url", "")
                    if not url:
                        continue

                    response = requests.head(url, timeout=5)
                    if response.status_code >= 400:
                        continue

                    alt = img.get("alt_text") or section_title
                    source = img.get("source", "")
                    lines.append(f"![{alt}]({url})")
                    if source:
                        lines.append(f"*Image source: {source}*")
                    lines.append("")
                    break

                except Exception:
                    continue

        lines.append(draft)
        lines.append("")

    # ── Citations ──────────────────────────────────────────────────────────────
    unique_citations = _deduplicate_citations(citations)
    if unique_citations:
        lines.append("---\n")
        lines.append("## References\n")
        for i, cit in enumerate(unique_citations, start=1):
            title_str = cit.get("source_title") or cit.get("source_url", "")
            url = cit.get("source_url", "")
            lines.append(f"{i}. [{title_str}]({url})\n")

    return "\n".join(lines)


def _deduplicate_citations(citations: list[CitationDict]) -> list[CitationDict]:
    seen: set[str] = set()
    unique = []
    for c in citations:
        url = c.get("source_url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(c)
    return unique


async def run_stitcher(state: BlogState) -> dict:
    """LangGraph node: Stitch Blog."""
    t0 = time.monotonic()

    final_blog = _build_final_blog(state)

    latency = time.monotonic() - t0
    metrics = state.get("metrics", {})
    node_latencies = dict(metrics.get("node_latencies", {}))
    node_latencies["stitcher"] = latency

    return {
        "final_blog": final_blog,
        "status": "persisting",
        "current_node": "persist_state",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": {**metrics, "node_latencies": node_latencies},
    }