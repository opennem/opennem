# pylint: disable=no-member
"""
generation_maximum and generation_maximum_date on units

Revision ID: 6e643632b05c
Revises: db4f1b02fdbc
Create Date: 2025-10-10 20:33:59.459593

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6e643632b05c'
down_revision = 'db4f1b02fdbc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('units', sa.Column('max_generation', sa.Numeric(precision=12, scale=4), nullable=True))
    op.add_column('units', sa.Column('max_generation_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('units', 'max_generation_date')
    op.drop_column('units', 'max_generation')
