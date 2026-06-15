"""
app/main.py
────────────
FastAPI application factory.

Architecture decisions:
- Lifespan context manager for startup/shutdown (no deprecated @app.on_event).
- CORS configured from settings for security.
- Tracing middleware on every request.
- All routers prefixed with /api/v1 for clean versioning.
- Static files served for the frontend at /app (when present).
"""

from __future__ import annotations
from pathlib import Path

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.middleware.tracing import TracingMiddleware
from app.api.routes import auth, blogs, workflow, metrics, preferences

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.APP_ENV == "development"
        else structlog.processors.JSONRenderer(),
    ]
)

logger = structlog.get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR.parent / "frontend"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    logger.info("starting_up", env=settings.APP_ENV)
    yield
    logger.info("shutting_down")


app = FastAPI(
    title="AI Blog Generation Platform",
    description="Multi-agent AI blog generator with human-in-the-loop approval.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(TracingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(blogs.router, prefix=PREFIX)
app.include_router(workflow.router, prefix=PREFIX)
app.include_router(metrics.router, prefix=PREFIX)
app.include_router(preferences.router, prefix=PREFIX)


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "env": settings.APP_ENV}


# ── Serve frontend static files ───────────────────────────────────────────────
# Mount AFTER API routes so /api/* always wins.
try:
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend"
    )
except Exception as e:
    print(f"Frontend mount failed: {e}")