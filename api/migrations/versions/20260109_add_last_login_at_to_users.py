"""Add last_login_at to users table

Revision ID: 20260109_add_last_login_at
Revises: 20260108_add_is_invalid
Create Date: 2026-01-09
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260109_add_last_login_at"
down_revision = "20260108_add_is_invalid"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add last_login_at column to users table."""
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Remove last_login_at column from users table."""
    op.drop_column("users", "last_login_at")
