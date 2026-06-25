"""
app/api/routes/workflow.py
───────────────────────────
Workflow endpoints:
  POST /workflow/start
  GET  /workflow/{job_id}
  POST /workflow/{job_id}/approve-plan
  POST /workflow/{job_id}/edit-plan
  POST /workflow/{job_id}/resume
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.db.models.user import User
from app.schemas import (
    ApprovePlanRequest,
    BlogCreateRequest,
    EditPlanRequest,
    ResumeRequest,
    WorkflowStartResponse,
    WorkflowStatusResponse,
)
from app.services import workflow_service
from app.services.guardrails import topic_judge

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/start", response_model=WorkflowStartResponse, status_code=202)
async def start_workflow(
    data: BlogCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a new blog generation workflow.
    Returns immediately after the Planner runs (workflow pauses for human approval).
    """

    # ---------- Topic Validation ----------
    validation = await topic_judge(data.topic)

    if not validation.allowed:
        raise HTTPException(
            status_code=400,
            detail=validation.reason,
        )

    result = await workflow_service.start_workflow(
        db,
        current_user.id, 
        data.topic,
        overrides={
        "preferred_tone": data.tone,
        "preferred_style": data.style,
        "technical_depth": data.technical_depth,
        "preferred_language": data.language,
        "preferred_word_count": data.word_count,
    },
    )

    return WorkflowStartResponse(
        job_id=result["job_id"],
        blog_id=result["blog_id"],
        status=result["status"],
        message="Workflow started. Waiting for plan approval.",
    )


@router.get("/{job_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll workflow status and retrieve the generated plan."""
    return await workflow_service.get_workflow_status(db, job_id)


@router.post("/{job_id}/approve-plan")
async def approve_plan(
    job_id: str,
    _: ApprovePlanRequest = ApprovePlanRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve the plan as-is and resume the workflow."""
    try:
        return await workflow_service.approve_plan(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{job_id}/edit-plan")
async def edit_plan(
    job_id: str,
    data: EditPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit an edited plan and resume the workflow."""

    edited = {
        "title": data.title,
        "sections": [s.model_dump() for s in data.sections],
        "estimated_word_count": data.estimated_word_count,
    }
    try:
        return await workflow_service.approve_plan(db, job_id, edited_plan=edited)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{job_id}/resume")
async def resume_workflow(
    job_id: str,
    _: ResumeRequest = ResumeRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generic resume endpoint (delegates to approve_plan without edits)."""
    try:
        return await workflow_service.approve_plan(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))