"""
app/api/routes/auth.py
───────────────────────
Authentication endpoints:
  POST /auth/register
  POST /auth/login
  POST /auth/refresh
  GET  /auth/me
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user account."""
    user = await auth_service.register(db, data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and return JWT tokens."""
    return await auth_service.login(db, data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a refresh token for a new token pair."""
    return await auth_service.refresh(db, data.refresh_token)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return current_user