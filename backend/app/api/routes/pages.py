"""
app/api/routes/pages.py
────────────────────────
Serves the built React SPA (frontend/dist/index.html) for every page route.
Routing between pages is handled client-side by react-router, so all of
these routes return the same shell document.
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
DIST_DIR = BASE_DIR / "frontend" / "dist"

router = APIRouter(prefix="", tags=["pages"])


def spa() -> FileResponse:
    """Return the React app shell for client-side routing."""
    return FileResponse(DIST_DIR / "index.html")


@router.get("/register", name="register_page")
async def register_page():
    """Serve the React app (registration screen)."""
    return spa()


@router.get("/login", name="login_page")
async def login_page():
    """Serve the React app (sign-in screen)."""
    return spa()


@router.get("/dashboard", name="dashboard_page")
async def dashboard_page():
    """Serve the React app (dashboard screen)."""
    return spa()


@router.get("/create", name="create_page")
async def create_page():
    """Serve the React app (new blog screen)."""
    return spa()


@router.get("/approval", name="approval_page")
async def approval_page():
    """Serve the React app (outline review screen)."""
    return spa()


@router.get("/viewer", name="viewer_page")
async def viewer_page():
    """Serve the React app (blog viewer screen)."""
    return spa()


@router.get("/settings", name="settings_page")
async def settings_page():
    """Serve the React app (settings screen)."""
    return spa()
