"""
app/api/routes/blogs.py
────────────────────────
Blog CRUD endpoints:
  POST   /blogs/create
  GET    /blogs
  GET    /blogs/{id}
  DELETE /blogs/{id}
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas import BlogListOut, BlogOut
from app.services import blog_service

router = APIRouter(prefix="/blogs", tags=["blogs"])


@router.get("", response_model=BlogListOut)
async def list_blogs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all blogs for the current user."""
    return await blog_service.list_blogs(db, current_user.id, skip, limit)


@router.get("/{blog_id}", response_model=BlogOut)
async def get_blog(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific blog by ID."""
    return await blog_service.get_blog(db, current_user.id, blog_id)


@router.delete("/{blog_id}", status_code=204)
async def delete_blog(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a blog."""
    await blog_service.delete_blog(db, current_user.id, blog_id)


@router.get("/{blog_id}/tokens", response_model=int)
async def get_blog_tokens(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get total tokens used for a blog."""
    tokens = await blog_service.get_blog_tokens(db, blog_id)
    print(f"Total tokens for blog {blog_id}: {tokens}")
    return tokens