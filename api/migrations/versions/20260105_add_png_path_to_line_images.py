"""Add png_path to line_images

Revision ID: 20260105_add_png_path
Revises: 20260105_create_default_admin
Create Date: 2026-01-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "20260105_add_png_path"
down_revision = "20260105_create_default_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add png_path column to line_images table if it does not exist."""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)

    columns = [col["name"] for col in inspector.get_columns("line_images")]

    if "png_path" not in columns:
        op.add_column(
            "line_images",
            sa.Column("png_path", sa.String(255), nullable=True)
        )


def downgrade() -> None:
    """Remove png_path column from line_images table if it exists."""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)

    columns = [col["name"] for col in inspector.get_columns("line_images")]

    if "png_path" in columns:
        op.drop_column("line_images", "png_path")
