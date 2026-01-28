"""Create default admin user

Revision ID: 20260105_create_default_admin
Revises:
Create Date: 2026-01-05
"""

import os
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260105_create_default_admin"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    admin_name = os.getenv("DEFAULT_ADMIN_NAME", "Admin")
    admin_password_hash = os.getenv(
        "DEFAULT_ADMIN_PASSWORD_HASH",
        "$2b$12$YqLrUafu.kKn7PYbnYBIROD8Zrak8LCXDDBGy/cb46R4ZJQArFama"  # pre-hashed bcrypt
    )

    op.execute(
        sa.text(
            """
            INSERT INTO users (id, name, email, hashed_password, role, is_active, created_at, updated_at)
            SELECT gen_random_uuid(), :name, :email, :password, 'admin', true, NOW(), NOW()
            WHERE NOT EXISTS (
                SELECT 1 FROM users WHERE email = :email
            )
            """
        ),
        {
            "name": admin_name,
            "email": admin_email,
            "password": admin_password_hash,
        },
    )


def downgrade() -> None:
    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")

    op.execute(
        sa.text("DELETE FROM users WHERE email = :email"),
        {"email": admin_email},
    )
