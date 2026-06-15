"""
app/api/routes/preferences.py
──────────────────────────────
User preferences:
  GET  /preferences
  PUT  /preferences
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.db.models.blog import UserPreference
from app.db.models.user import User
from app.schemas import PreferenceOut, PreferenceUpdate

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=PreferenceOut)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    pref = result.scalar_one_or_none()
    if pref is None:
        # Create defaults
        pref = UserPreference(user_id=current_user.id)
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
    return pref


@router.put("", response_model=PreferenceOut)
async def update_preferences(
    data: PreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    pref = result.scalar_one_or_none()
    if pref is None:
        pref = UserPreference(user_id=current_user.id)
        db.add(pref)
        await db.flush()

    update_vals = data.model_dump(exclude_none=True)
    if update_vals:
        await db.execute(
            update(UserPreference)
            .where(UserPreference.user_id == current_user.id)
            .values(**update_vals)
        )

    await db.commit()
    await db.refresh(pref)
    return pref