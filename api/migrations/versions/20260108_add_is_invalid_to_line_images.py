"""Add is_invalid to line_images

Revision ID: 20260108_add_is_invalid
Revises: 20260105_add_png_path
Create Date: 2026-01-08
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260108_add_is_invalid"
down_revision = "20260105_add_png_path"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add is_invalid column to line_images table."""
    op.add_column(
        "line_images",
        sa.Column("is_invalid", sa.Boolean(), nullable=False, server_default=sa.false())
    )
    # Drop server default after setting initial values
    op.alter_column("line_images", "is_invalid", server_default=None)


def downgrade() -> None:
    """Remove is_invalid column from line_images table."""
    op.drop_column("line_images", "is_invalid")
