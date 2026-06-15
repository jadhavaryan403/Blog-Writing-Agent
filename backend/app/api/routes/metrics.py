"""
app/api/routes/metrics.py
──────────────────────────
Metrics endpoints:
  GET /metrics/usage
  GET /metrics/agent-runs
  GET /metrics/blog-history
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas import AgentRunsResponse, BlogHistoryItem, UsageMetricOut
from app.services import metrics_service

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/usage", response_model=UsageMetricOut)
async def get_usage(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return aggregate usage metrics for the current user."""
    row = await metrics_service.get_usage(db, current_user.id)
    if row is None:
        # Return zeroed metrics
        return UsageMetricOut(
            total_requests=0,
            total_tokens=0,
            total_cost=0.0,
            average_latency=0.0,
            last_request_at=None,
        )
    return row


@router.get("/agent-runs", response_model=AgentRunsResponse)
async def get_agent_runs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return agent execution history for the current user."""
    return await metrics_service.get_agent_runs(db, current_user.id, skip, limit)


@router.get("/blog-history", response_model=list[BlogHistoryItem])
async def get_blog_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return blog generation history for the current user."""
    return await metrics_service.get_blog_history(db, current_user.id, skip, limit)