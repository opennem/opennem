# pylint: disable=no-member
"""
milestones pct_change field

Revision ID: 4ae275627ed5
Revises: 06f2e270e664
Create Date: 2025-03-25 04:56:38.692925

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4ae275627ed5'
down_revision = '06f2e270e664'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('milestones', sa.Column('pct_change', sa.Numeric(precision=12, scale=2), nullable=True))


def downgrade() -> None:
    op.drop_column('milestones', 'pct_change')
