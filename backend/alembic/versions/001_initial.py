"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── user_preferences ──────────────────────────────────────────────────────
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True),
        sa.Column("preferred_tone", sa.String(50), server_default="professional"),
        sa.Column("preferred_style", sa.String(50), server_default="informative"),
        sa.Column("preferred_word_count", sa.Integer(), server_default="1500"),
        sa.Column("preferred_language", sa.String(20), server_default="English"),
        sa.Column("technical_depth", sa.String(20), server_default="intermediate"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── usage_metrics ─────────────────────────────────────────────────────────
    op.create_table(
        "usage_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True),
        sa.Column("total_requests", sa.Integer(), server_default="0"),
        sa.Column("total_tokens", sa.BigInteger(), server_default="0"),
        sa.Column("total_cost", sa.Float(), server_default="0"),
        sa.Column("average_latency", sa.Float(), server_default="0"),
        sa.Column("last_request_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── blogs ──────────────────────────────────────────────────────────────────
    op.create_table(
        "blogs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), index=True),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("topic", sa.String(500), nullable=False),
        sa.Column("status", sa.String(50), server_default="pending", index=True),
        sa.Column("final_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── workflow_states ───────────────────────────────────────────────────────
    op.create_table(
        "workflow_states",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("blog_id", sa.Integer(), sa.ForeignKey("blogs.id", ondelete="CASCADE"), index=True),
        sa.Column("job_id", sa.String(100), unique=True, index=True, nullable=False),
        sa.Column("current_node", sa.String(100), nullable=True),
        sa.Column("serialized_state", JSONB, nullable=True),
        sa.Column("status", sa.String(50), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── citations ─────────────────────────────────────────────────────────────
    op.create_table(
        "citations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("blog_id", sa.Integer(), sa.ForeignKey("blogs.id", ondelete="CASCADE"), index=True),
        sa.Column("section_id", sa.Integer(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_title", sa.String(500), nullable=True),
    )

    # ── blog_images ───────────────────────────────────────────────────────────
    op.create_table(
        "blog_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("blog_id", sa.Integer(), sa.ForeignKey("blogs.id", ondelete="CASCADE"), index=True),
        sa.Column("section_id", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("image_source", sa.String(500), nullable=True),
        sa.Column("alt_text", sa.String(500), nullable=True),
    )

    # ── agent_runs ────────────────────────────────────────────────────────────
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("blog_id", sa.Integer(), sa.ForeignKey("blogs.id", ondelete="CASCADE"), index=True),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("tokens_used", sa.Integer(), server_default="0"),
        sa.Column("cost", sa.Float(), server_default="0"),
        sa.Column("latency", sa.Float(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("agent_runs")
    op.drop_table("blog_images")
    op.drop_table("citations")
    op.drop_table("workflow_states")
    op.drop_table("blogs")
    op.drop_table("usage_metrics")
    op.drop_table("user_preferences")
    op.drop_table("users")