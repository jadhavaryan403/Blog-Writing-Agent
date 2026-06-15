"""
app/services/blog_service.py
──────────────────────────────
Blog CRUD service.
"""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.blog import Blog, Citation, BlogImage, AgentRun


async def list_blogs(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20) -> dict:
    count_q = await db.execute(
        select(func.count()).select_from(Blog).where(Blog.user_id == user_id)
    )
    total = count_q.scalar_one()

    result = await db.execute(
        select(Blog)
        .where(Blog.user_id == user_id)
        .order_by(Blog.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    return {"items": items, "total": total}


async def get_blog(db: AsyncSession, user_id: int, blog_id: int) -> Blog:
    result = await db.execute(
        select(Blog).where(Blog.id == blog_id, Blog.user_id == user_id)
    )
    blog = result.scalar_one_or_none()
    if blog is None:
        raise HTTPException(status_code=404, detail="Blog not found")
    return blog


async def delete_blog(db: AsyncSession, user_id: int, blog_id: int) -> None:
    blog = await get_blog(db, user_id, blog_id)
    await db.delete(blog)
    await db.commit()


async def get_blog_tokens(db: AsyncSession, blog_id: int) -> int:
    result = await db.execute(
        select(func.sum(AgentRun.tokens_used)).where(AgentRun.blog_id == blog_id)
    )
    total_tokens = result.scalar_one() or 0
    return total_tokens