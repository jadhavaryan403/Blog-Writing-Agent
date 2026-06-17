"""Add edit_version to blogs

Revision ID: 002_edit_version
Revises: 001_initial
Create Date: 2024-01-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "002_edit_version"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add edit_version to blogs so the API can report which revision a blog is on
    op.add_column(
        "blogs",
        sa.Column("edit_version", sa.Integer(), server_default="1", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("blogs", "edit_version")