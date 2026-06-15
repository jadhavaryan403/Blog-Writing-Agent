"""
app/langgraph/agents/persist.py
─────────────────────────────────
Persist State Node — writes the completed blog, citations, images,
and agent run metrics to PostgreSQL at the end of the workflow.

This is the only node that directly accesses the database.
It uses a fresh sync-compatible approach via async session.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.blog import Blog, Citation, BlogImage, AgentRun, UsageMetric
from app.db.session import AsyncSessionLocal
from app.langgraph.state import BlogState


async def run_persist(state: BlogState) -> dict:
    """LangGraph node: Persist State."""
    t0 = time.monotonic()

    async with AsyncSessionLocal() as db:
        blog_id = state.get("blog_id")
        if not blog_id:
            return {"status": "error", "error_message": "blog_id missing in state"}

        # ── Update Blog record ─────────────────────────────────────────────────
        await db.execute(
            update(Blog)
            .where(Blog.id == blog_id)
            .values(
                title=state.get("title"),
                final_content=state.get("final_blog"),
                status="completed",
            )
        )

        # ── Persist Citations ──────────────────────────────────────────────────
        for cit in state.get("citations", []):
            db.add(Citation(
                blog_id=blog_id,
                section_id=cit.get("section_idx"),
                source_url=cit.get("source_url", ""),
                source_title=cit.get("source_title", ""),
            ))

        # ── Persist Images ─────────────────────────────────────────────────────
        for img in state.get("image_results", []):
            if img.get("image_url"):
                db.add(BlogImage(
                    blog_id=blog_id,
                    section_id=img.get("section_idx"),
                    image_url=img.get("image_url", ""),
                    image_source=img.get("source", ""),
                    alt_text=img.get("alt_text", ""),
                ))

        # ── Persist AgentRun metrics ──────────────────────────────────────────
        metrics = state.get("metrics", {})
        node_latencies: dict = metrics.get("node_latencies", {})
        for node_name, latency in node_latencies.items():
            db.add(AgentRun(
                blog_id=blog_id,
                agent_name=node_name,
                tokens_used=metrics.get("node_token", {}).get(node_name, 0),
                cost=0.0,
                latency=latency,
            ))

        # ── Update global UsageMetric for user ────────────────────────────────
        user_id = state.get("user_id")
        if user_id:
            result = await db.execute(select(UsageMetric).where(UsageMetric.user_id == user_id))
            usage_row = result.scalar_one_or_none()
            total_tokens = metrics.get("total_tokens", 0)
            total_cost = metrics.get("total_cost", 0.0)
            total_latency = sum(node_latencies.values())

            if usage_row:
                new_count = usage_row.total_requests + 1
                new_avg_latency = (
                    (usage_row.average_latency * usage_row.total_requests + total_latency)
                    / new_count
                )
                await db.execute(
                    update(UsageMetric)
                    .where(UsageMetric.user_id == user_id)
                    .values(
                        total_requests=new_count,
                        total_tokens=usage_row.total_tokens + total_tokens,
                        total_cost=usage_row.total_cost + total_cost,
                        average_latency=new_avg_latency,
                        last_request_at=datetime.now(timezone.utc),
                    )
                )
            else:
                db.add(UsageMetric(
                    user_id=user_id,
                    total_requests=1,
                    total_tokens=total_tokens,
                    total_cost=total_cost,
                    average_latency=total_latency,
                    last_request_at=datetime.now(timezone.utc),
                ))

        await db.commit()

    latency = time.monotonic() - t0

    return {
        "status": "completed",
        "current_node": "END",
    }