"""Create default admin user

Revision ID: 20260105_create_default_admin
Revises: 
Create Date: 2026-01-05
"""

import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from app.models import User
from app.security import hash_password

# revision identifiers, used by Alembic.
revision = "20260105_create_default_admin"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ensure a default admin account exists."""
    bind = op.get_bind()
    session = Session(bind=bind)

    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "ChangeMe123!")
    admin_name = os.getenv("DEFAULT_ADMIN_NAME", "Admin")

    try:
        existing = session.query(User).filter(User.email == admin_email).first()
        if existing:
            updated = False
            if existing.role != "admin":
                existing.role = "admin"
                updated = True
            if not existing.is_active:
                existing.is_active = True
                updated = True
            if updated:
                session.commit()
            return

        admin_user = User(
            name=admin_name,
            email=admin_email,
            hashed_password=hash_password(admin_password),
            role="admin",
            is_active=True,
        )
        session.add(admin_user)
        session.commit()
    finally:
        session.close()


def downgrade() -> None:
    """Remove the default admin account created by this migration."""
    bind = op.get_bind()
    session = Session(bind=bind)
    admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")

    try:
        user = session.query(User).filter(User.email == admin_email).first()
        if user:
            session.delete(user)
            session.commit()
    finally:
        session.close()
