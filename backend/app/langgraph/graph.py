"""
app/langgraph/graph.py
───────────────────────
Main LangGraph workflow graph.

Workflow:
  START
    → planner
    → human_approval   ← INTERRUPT here (wait for human)
    → router           ← decides: research? skip?
    → researcher       (conditional)
    → generate         (writer)
    → image_planner
    → image_search
    → stitch_blog
    → persist_state
    → END

Human-in-the-Loop:
  The graph interrupts at `human_approval`.
  The API layer persists the state, returns the plan to the frontend,
  and resumes execution after the user approves / edits the plan.

Checkpointing:
  We use an in-memory AsyncSqliteSaver for development and swap to
  PostgresSaver in production. The job_id serves as the thread_id so
  state is retrievable between API calls.
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END as LG_END
from langgraph.checkpoint.memory import MemorySaver

from app.langgraph.state import BlogState
from app.langgraph.agents.planner import run_planner
from app.langgraph.agents.researcher import run_researcher
from app.langgraph.agents.writer import run_writer
from app.langgraph.agents.image_planner import run_image_planner
from app.langgraph.agents.image_search import run_image_search
from app.langgraph.agents.stitcher import run_stitcher
from app.langgraph.agents.persist import run_persist


# ── Human approval placeholder node ──────────────────────────────────────────
# This node is a passthrough; the actual interrupt is declared via
# interrupt_before in the compile() call.

async def human_approval_node(state: BlogState) -> dict:
    """
    Passthrough node that the graph pauses BEFORE executing.
    When resumed, the state will have been updated externally
    (title / sections / estimated_word_count edited by the user).
    """
    return {"human_approved": True, "status": "routing", "current_node": "router"}


# ── Routing functions ─────────────────────────────────────────────────────────

def route_after_human(state: BlogState) -> str:
    """Always go to router after human approval."""
    return "router"


def route_research(state: BlogState) -> str:
    """Decide whether to run researcher or skip straight to writer."""
    if state.get("research_required", False):
        return "researcher"
    return "generate"



# ── Router node (explicit graph node) ────────────────────────────────────────

async def router_node(state: BlogState) -> dict:
    """Thin node — routing logic handled by conditional edges."""
    return {"current_node": "router"}


# ── Build the graph ───────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(BlogState)

    # Register nodes
    graph.add_node("planner", run_planner)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("router", router_node)
    graph.add_node("researcher", run_researcher)
    graph.add_node("generate", run_writer)
    graph.add_node("image_planner", run_image_planner)
    graph.add_node("image_search", run_image_search)
    graph.add_node("stitch_blog", run_stitcher)
    graph.add_node("persist_state", run_persist)

    # ── Edges ─────────────────────────────────────────────────────────────────
    graph.set_entry_point("planner")
    graph.add_edge("planner", "human_approval")
    graph.add_edge("human_approval", "router")

    # After router: conditional — research or write
    graph.add_conditional_edges("router", route_research, {
        "researcher": "researcher",
        "generate": "generate",
    })

    graph.add_edge("researcher", "generate")
    graph.add_edge("generate", "image_planner")
    graph.add_edge("image_planner", "image_search")
    graph.add_edge("image_search", "stitch_blog")
    graph.add_edge("stitch_blog", "persist_state")
    graph.add_edge("persist_state", LG_END)

    return graph


# ── Compiled graph (singleton — reused across requests) ──────────────────────
# MemorySaver stores checkpoints in-memory keyed by thread_id (= job_id).
# For multi-process / persistent deployments, swap to AsyncSqliteSaver or
# a custom PostgreSQL checkpointer.

_checkpointer = MemorySaver()

compiled_graph = build_graph().compile(
    checkpointer=_checkpointer,
    interrupt_before=["human_approval"],   # ← INTERRUPT before human_approval node
)