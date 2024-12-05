# pylint: disable=no-member
"""
mv_facility_unit_daily refresh policy

Revision ID: f4b96c795fe1
Revises: 0ef382d2ee54
Create Date: 2024-12-06 10:27:35.519399

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'f4b96c795fe1'
down_revision = '0ef382d2ee54'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SELECT remove_continuous_aggregate_policy('mv_facility_unit_daily');")
    op.execute(
        """SELECT add_continuous_aggregate_policy(
        'mv_facility_unit_daily',
        start_offset => INTERVAL '30 days',
        end_offset => NULL,
        schedule_interval => INTERVAL '1 hour'
        );"""
    )


def downgrade() -> None:
    pass
