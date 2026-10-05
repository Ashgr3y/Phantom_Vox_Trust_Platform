"""Initial Phantom Vox schema.

Revision ID: 20260922_0001
Revises: None
"""

from alembic import op
from app.db.session import Base

revision = "20260922_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The declarative metadata is authoritative for this initial local-release
    # migration. Future production migrations should use explicit generated DDL.
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
