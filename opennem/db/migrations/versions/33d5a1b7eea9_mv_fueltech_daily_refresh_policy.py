# pylint: disable=no-member
"""
mv_fueltech_daily refresh policy

Revision ID: 33d5a1b7eea9
Revises: f4b96c795fe1
Create Date: 2024-12-06 10:29:37.781349

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '33d5a1b7eea9'
down_revision = 'f4b96c795fe1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SELECT remove_continuous_aggregate_policy('mv_fueltech_daily');")
    op.execute(
        """SELECT add_continuous_aggregate_policy(
        'mv_fueltech_daily',
        start_offset => INTERVAL '30 days',
        end_offset => NULL,
        schedule_interval => INTERVAL '1 hour'
        );"""
    )


def downgrade() -> None:
    pass
