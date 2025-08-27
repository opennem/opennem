# pylint: disable=no-member
"""
balancing summary curtailment fields

Revision ID: 9436b8ba01e9
Revises: a48ebf979bce
Create Date: 2025-08-18 00:04:50.015483

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '9436b8ba01e9'
down_revision = 'a48ebf979bce'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('balancing_summary', sa.Column('ss_solar_uigf', sa.Numeric(precision=20, scale=6), nullable=True))
    op.add_column('balancing_summary', sa.Column('ss_solar_clearedmw', sa.Numeric(precision=20, scale=6), nullable=True))
    op.add_column('balancing_summary', sa.Column('ss_wind_uigf', sa.Numeric(precision=20, scale=6), nullable=True))
    op.add_column('balancing_summary', sa.Column('ss_wind_clearedmw', sa.Numeric(precision=20, scale=6), nullable=True))


def downgrade() -> None:
    op.drop_column('balancing_summary', 'ss_wind_clearedmw')
    op.drop_column('balancing_summary', 'ss_wind_uigf')
    op.drop_column('balancing_summary', 'ss_solar_clearedmw')
    op.drop_column('balancing_summary', 'ss_solar_uigf')
