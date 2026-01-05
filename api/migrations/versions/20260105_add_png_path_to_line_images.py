"""Add png_path to line_images

Revision ID: 20260105_add_png_path
Revises: 20260105_create_default_admin
Create Date: 2026-01-05
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260105_add_png_path"
down_revision = "20260105_create_default_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add png_path column to line_images table."""
    op.add_column(
        "line_images",
        sa.Column("png_path", sa.String(255), nullable=True)
    )


def downgrade() -> None:
    """Remove png_path column from line_images table."""
    op.drop_column("line_images", "png_path")
