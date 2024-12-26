# pylint: disable=no-member
"""
milestones value field data type

Revision ID: 67cc493a27d4
Revises: 1873cc2ad112
Create Date: 2024-12-27 08:04:11.375908

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67cc493a27d4'
down_revision = '1873cc2ad112'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('milestones', 'value',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=20, scale=6),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('milestones', 'value',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=False)
