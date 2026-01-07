# pylint: disable=no-member
"""
rename to max_generation_interval

Revision ID: b443948c1a49
Revises: 6e643632b05c
Create Date: 2025-10-10 20:42:13.838498

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b443948c1a49'
down_revision = '6e643632b05c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('units', 'max_generation_date', new_column_name='max_generation_interval')


def downgrade() -> None:
    op.alter_column('units', 'max_generation_interval', new_column_name='max_generation_date')
