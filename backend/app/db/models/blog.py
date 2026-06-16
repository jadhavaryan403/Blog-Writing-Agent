"""
app/db/models/blog.py
──────────────────────
SQLAlchemy ORM models:
  Blog, WorkflowState, Citation, BlogImage, AgentRun, UserPreference, UsageMetric
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, ForeignKey,
    Integer, String, Text, func, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Blog(Base):
    __tablename__ = "blogs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    final_content: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    edit_version: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="blogs")  # noqa: F821
    workflow_states: Mapped[list["WorkflowState"]] = relationship(
        "WorkflowState", back_populates="blog", lazy="select"
    )
    citations: Mapped[list["Citation"]] = relationship("Citation", back_populates="blog")
    images: Mapped[list["BlogImage"]] = relationship("BlogImage", back_populates="blog")
    agent_runs: Mapped[list["AgentRun"]] = relationship("AgentRun", back_populates="blog")


class WorkflowState(Base):
    """Persists LangGraph state snapshots so the workflow is resumable."""

    __tablename__ = "workflow_states"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    blog_id: Mapped[int] = mapped_column(ForeignKey("blogs.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    current_node: Mapped[Optional[str]] = mapped_column(String(100))
    serialized_state: Mapped[Optional[dict]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    blog: Mapped["Blog"] = relationship("Blog", back_populates="workflow_states")


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    blog_id: Mapped[int] = mapped_column(ForeignKey("blogs.id", ondelete="CASCADE"), index=True)
    section_id: Mapped[Optional[int]] = mapped_column(Integer)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_title: Mapped[Optional[str]] = mapped_column(String(500))

    blog: Mapped["Blog"] = relationship("Blog", back_populates="citations")


class BlogImage(Base):
    __tablename__ = "blog_images"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    blog_id: Mapped[int] = mapped_column(ForeignKey("blogs.id", ondelete="CASCADE"), index=True)
    section_id: Mapped[Optional[int]] = mapped_column(Integer)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    image_source: Mapped[Optional[str]] = mapped_column(String(500))
    alt_text: Mapped[Optional[str]] = mapped_column(String(500))

    blog: Mapped["Blog"] = relationship("Blog", back_populates="images")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    blog_id: Mapped[int] = mapped_column(ForeignKey("blogs.id", ondelete="CASCADE"), index=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    latency: Mapped[float] = mapped_column(Float, default=0.0)  # seconds
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    blog: Mapped["Blog"] = relationship("Blog", back_populates="agent_runs")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    preferred_tone: Mapped[str] = mapped_column(String(50), default="professional")
    preferred_style: Mapped[str] = mapped_column(String(50), default="informative")
    preferred_word_count: Mapped[int] = mapped_column(Integer, default=1500)
    preferred_language: Mapped[str] = mapped_column(String(20), default="English")
    technical_depth: Mapped[str] = mapped_column(String(20), default="intermediate")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="preferences")


class UsageMetric(Base):
    __tablename__ = "usage_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    total_requests: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    average_latency: Mapped[float] = mapped_column(Float, default=0.0)
    last_request_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship("User", back_populates="usage_metrics")