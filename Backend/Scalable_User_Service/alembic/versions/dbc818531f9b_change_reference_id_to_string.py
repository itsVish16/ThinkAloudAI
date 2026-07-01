"""Change reference_id to String

Revision ID: dbc818531f9b
Revises: 722034068122
Create Date: 2026-06-21 00:47:13.152218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dbc818531f9b'
down_revision: Union[str, Sequence[str], None] = '722034068122'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('learning_events', 'reference_id',
               existing_type=sa.INTEGER(),
               type_=sa.String(length=255),
               existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('learning_events', 'reference_id',
               existing_type=sa.String(length=255),
               type_=sa.INTEGER(),
               existing_nullable=True)
