"""
app/schemas/
─────────────
All Pydantic request / response schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ═══════════════════════════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# User Preferences
# ═══════════════════════════════════════════════════════════════════════════════

class PreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    preferred_tone: str
    preferred_style: str
    preferred_word_count: int
    preferred_language: str
    technical_depth: str
    updated_at: datetime


class PreferenceUpdate(BaseModel):
    preferred_tone: Optional[str] = None
    preferred_style: Optional[str] = None
    preferred_word_count: Optional[int] = Field(None, ge=100, le=10000)
    preferred_language: Optional[str] = None
    technical_depth: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Blog
# ═══════════════════════════════════════════════════════════════════════════════

class BlogCreateRequest(BaseModel):
    topic: str

    tone: str | None = None
    style: str | None = None
    technical_depth: str | None = None
    language: str | None = None
    word_count: int | None = None


class BlogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    topic: str
    title: Optional[str]
    status: str
    final_content: Optional[str]
    created_at: datetime
    updated_at: datetime


class BlogListOut(BaseModel):
    items: list[BlogOut]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
# Workflow / Plan
# ═══════════════════════════════════════════════════════════════════════════════

class SectionSchema(BaseModel):
    title: str
    description: str = ""
    word_count: int = 300


class PlanSchema(BaseModel):
    title: str
    sections: list[SectionSchema]
    research_required: bool
    research_tasks: dict[int, str] = {}
    estimated_word_count: int = 1500


class WorkflowStartResponse(BaseModel):
    job_id: str
    blog_id: int
    status: str = "planning"
    message: str


class WorkflowStatusResponse(BaseModel):
    job_id: str
    blog_id: int
    status: str
    current_node: Optional[str]
    plan: Optional[PlanSchema] = None
    final_blog: Optional[str] = None
    error: Optional[str] = None


class ApprovePlanRequest(BaseModel):
    """Human-in-the-loop: approve plan as-is."""
    pass


class EditPlanRequest(BaseModel):
    """Human-in-the-loop: submit edited plan before resuming."""
    title: str
    sections: list[SectionSchema]
    estimated_word_count: int = Field(..., ge=100)


class ResumeRequest(BaseModel):
    """Generic resume — used after any interrupt."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics
# ═══════════════════════════════════════════════════════════════════════════════

class UsageMetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_requests: int
    total_tokens: int
    total_cost: float
    average_latency: float
    last_request_at: Optional[datetime]


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    agent_name: str
    tokens_used: int
    cost: float
    latency: float
    created_at: datetime


class AgentRunsResponse(BaseModel):
    items: list[AgentRunOut]
    total: int


class BlogHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: Optional[str]
    topic: str
    status: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# Edit Section
# ═══════════════════════════════════════════════════════════════════════════════


class SectionListItem(BaseModel):
    section_id: str         
    title: str
    word_count: int
    has_content: bool
 
 
class EditSectionRequest(BaseModel):
    section_id: str = Field(
        ...,
        description="Zero-based section index (as string) or exact section title.",
        examples=["0", "Introduction", "3"],
    )
    instruction: str = Field(
        ...,
        min_length=5,
        max_length=1000,
        description="Natural-language instruction for the editor agent.",
        examples=[
            "Make this section more technical and add LangGraph code examples.",
            "Rewrite for a beginner audience — avoid jargon.",
            "Add more details about the performance benchmarks.",
        ],
    )
 
 
class EditSectionResponse(BaseModel):
    updated_blog: str
    updated_section: str
    section_title: str
    section_idx: int
    version: int