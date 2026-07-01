"""Add UniqueConstraint

Revision ID: 722034068122
Revises: 6fecf64a9f97
Create Date: 2026-06-20 23:46:56.591478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '722034068122'
down_revision: Union[str, Sequence[str], None] = '6fecf64a9f97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint("uix_user_id_domain", "user_skills", ["user_id", "domain"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_unique_constraint("uix_user_id_domain", "user_skills")
