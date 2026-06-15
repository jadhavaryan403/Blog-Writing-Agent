"""
app/db/models/user.py
──────────────────────
SQLAlchemy ORM model for User.
"""

from datetime import datetime, timezone
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    blogs: Mapped[list["Blog"]] = relationship("Blog", back_populates="user", lazy="select")  # noqa: F821
    preferences: Mapped["UserPreference"] = relationship(  # noqa: F821
        "UserPreference", back_populates="user", uselist=False, lazy="select"
    )
    usage_metrics: Mapped["UsageMetric"] = relationship(  # noqa: F821
        "UsageMetric", back_populates="user", uselist=False, lazy="select"
    )