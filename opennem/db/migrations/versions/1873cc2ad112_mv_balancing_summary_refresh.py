# pylint: disable=no-member
"""
mv_balancing_summary refresh

Revision ID: 1873cc2ad112
Revises: 33d5a1b7eea9
Create Date: 2024-12-15 13:16:25.853155

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "1873cc2ad112"
down_revision = "33d5a1b7eea9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SELECT remove_continuous_aggregate_policy('mv_balancing_summary');")
    op.execute(
        """SELECT add_continuous_aggregate_policy(
        'mv_balancing_summary',
        start_offset => INTERVAL '1 day',
        end_offset => NULL,
        schedule_interval => INTERVAL '5 minutes')
        """
    )


def downgrade() -> None:
    pass
