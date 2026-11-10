"""
app/langgraph/state.py
───────────────────────
Comprehensive LangGraph state model using TypedDict + Pydantic helpers.

Design decision: Use TypedDict for LangGraph compatibility (the framework
requires subscriptable dict-like types for state). Pydantic models are used
for validating sub-structures at the agent boundary.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from typing import Annotated, TypedDict


# ── Sub-structure helpers (plain dicts — serialisable to JSON) ────────────────

class SectionDict(TypedDict, total=False):
    title: str
    description: str
    word_count: int
    draft: str          # populated after Writer agent


class ResearchResultDict(TypedDict, total=False):
    task_id: str
    task: str
    content: str
    sources: list[dict]   # [{url, title}]


class CitationDict(TypedDict, total=False):
    section_idx: int
    source_url: str
    source_title: str


class ImageQueryDict(TypedDict, total=False):
    section_idx: int
    query: str


class ImageResultDict(TypedDict, total=False):
    section_idx: int
    image_url: str
    title: str
    source: str
    alt_text: str


class MetricsDict(TypedDict, total=False):
    total_tokens: int
    total_cost: float
    node_latencies: dict[str, float]   # node_name → seconds
    node_token: dict[str, int]   # node_name → tokens used



def last_value(a, b):
    """Keep the newest non-None value when parallel nodes both write the key."""
    return b if b is not None else a

def merge_metrics(a: dict | None, b: dict | None) -> dict:
    a, b = a or {}, b or {}
    return {
        "total_tokens": a.get("total_tokens", 0) + b.get("total_tokens", 0),
        "total_cost": a.get("total_cost", 0.0) + b.get("total_cost", 0.0),
        "node_latencies": {**a.get("node_latencies", {}), **b.get("node_latencies", {})},
        "node_token": {**a.get("node_token", {}), **b.get("node_token", {})},
    }

# ── Master BlogState ──────────────────────────────────────────────────────────

class BlogState(TypedDict, total=False):
    # Identity
    job_id: str
    user_id: int
    blog_id: int

    # Topic & Plan
    topic: str
    title: str
    sections: list[SectionDict]
    research_required: bool
    research_tasks: dict[int, str]   # task_id → specific research query
    estimated_word_count: int

    # User preferences (injected before planning)
    user_preferences: dict[str, Any]

    # Research
    research_results: list[ResearchResultDict]

    # Writing
    section_drafts: list[str]   # ordered, one per section

    # Images
    image_queries: list[ImageQueryDict]
    image_results: list[ImageResultDict]

    # Citations
    citations: list[CitationDict]

    # Final output
    final_blog: str

    # Workflow control
    status: Annotated[str, last_value]          # pending | planning | awaiting_approval | researching
                                                # writing | image_planning
                                                # image_searching | stitching | persisting | completed | error
    current_node: Annotated[str, last_value]
    error_message: str

    # Human-in-the-loop flag: set to True after human approves/edits plan
    human_approved: bool

    # Observability
    metrics: Annotated[MetricsDict, merge_metrics]
    created_at: str   # ISO datetime string
    updated_at: Annotated[str, last_value]
