"""
app/services/metrics_service.py
────────────────────────────────
Metrics service — usage stats, agent run history, blog history.
"""

from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.blog import AgentRun, Blog, UsageMetric


async def get_usage(db: AsyncSession, user_id: int) -> UsageMetric | None:
    result = await db.execute(
        select(UsageMetric).where(UsageMetric.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_agent_runs(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 50
) -> dict:
    # Join through Blog to filter by user
    q = (
        select(AgentRun)
        .join(Blog, AgentRun.blog_id == Blog.id)
        .where(Blog.user_id == user_id)
        .order_by(AgentRun.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(q)
    items = result.scalars().all()

    count_q = (
        select(func.count())
        .select_from(AgentRun)
        .join(Blog, AgentRun.blog_id == Blog.id)
        .where(Blog.user_id == user_id)
    )
    count_result = await db.execute(count_q)
    total = count_result.scalar_one()

    return {"items": items, "total": total}


async def get_blog_history(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20
) -> list[Blog]:
    result = await db.execute(
        select(Blog)
        .where(Blog.user_id == user_id)
        .order_by(Blog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()