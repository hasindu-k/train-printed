"""Add name to documents table

Revision ID: 20260225_add_name_to_documents
Revises: 20260109_add_last_login_at
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260225_add_name_to_documents"
down_revision = "20260109_add_last_login_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add name column to documents table and backfill existing rows."""
    op.add_column("documents", sa.Column("name", sa.String(length=255), nullable=True))
    op.execute("UPDATE documents SET name = original_filename WHERE name IS NULL")
    op.alter_column("documents", "name", existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    """Remove name column from documents table."""
    op.drop_column("documents", "name")
