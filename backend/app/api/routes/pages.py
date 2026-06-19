from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend/pages"

router = APIRouter(prefix="", tags=["pages"])
templates = Jinja2Templates(directory=str(FRONTEND_DIR))


@router.get("/register", name="register_page")
async def register_page(request: Request):
    """Render the registration page."""
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"request": request}
        )


@router.get("/login", name="login_page")
async def login_page(request: Request):
    """Render the login page."""
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"request": request}
        )


@router.get("/dashboard", name="dashboard_page")
async def dashboard_page(request: Request):
    """Render the dashboard page."""
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"request": request}
        )


@router.get("/create", name="create_page")
async def create_page(request: Request):
    """Render the create page."""
    return templates.TemplateResponse(
        request=request,
        name="create.html",
        context={"request": request}
        )


@router.get("/approval", name="approval_page")
async def approval_page(request: Request):
    """Render the approval page."""
    return templates.TemplateResponse(
        request=request,
        name="approval.html",
        context={"request": request}
        )


@router.get("/viewer", name="viewer_page")
async def viewer_page(request: Request):
    """Render the viewer page."""
    return templates.TemplateResponse(
        request=request,
        name="viewer.html",
        context={"request": request}
        )


@router.get("/settings", name="settings_page")
async def settings_page(request: Request):
    """Render the settings page."""
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={"request": request}
        )