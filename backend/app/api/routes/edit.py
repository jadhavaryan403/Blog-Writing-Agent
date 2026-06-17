"""
app/api/routes/edit.py
───────────────────────
Section editing endpoints:

  GET  /blogs/{blog_id}/sections          — list all sections (title + id)
  POST /blogs/{blog_id}/edit-section      — edit one section with an instruction
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas import (
    EditSectionRequest,
    EditSectionResponse,
    SectionListItem,
)
from app.services.edit_service import edit_blog_section, get_blog_sections

router = APIRouter(prefix="/blogs", tags=["section-editing"])


@router.get("/{blog_id}/sections", response_model=list[SectionListItem])
async def list_sections(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return all section titles and IDs for a blog.
    The frontend uses this to populate the section picker — users never
    type section numbers manually.
    """
    return await get_blog_sections(db, blog_id, current_user.id)


@router.post("/{blog_id}/edit-section", response_model=EditSectionResponse)
async def edit_section_endpoint(
    blog_id: int,
    data: EditSectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Edit a single blog section using a natural-language instruction.

    The editor agent:
    - Receives the full blog context (title, outline, surrounding sections)
    - Receives the current section content and any research notes
    - Applies the instruction and returns only the updated section
    - The full blog is re-stitched and persisted automatically
    """
    return await edit_blog_section(
        db=db,
        blog_id=blog_id,
        user_id=current_user.id,
        section_id=data.section_id,
        instruction=data.instruction,
    )