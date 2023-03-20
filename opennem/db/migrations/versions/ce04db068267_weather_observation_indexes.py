# pylint: disable=no-member
"""
weather observation indexes

Revision ID: ce04db068267
Revises: 9198c786d9c9
Create Date: 2023-03-20 22:27:13.356374

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ce04db068267"
down_revision = "9198c786d9c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """create index if not exists
            idx_bom_observation_month_aest
        on bom_observation (date_trunc('month', observation_time at time zone 'AEST'), station_id)"""
    )
    op.execute(
        """create index if not exists
            idx_bom_observation_month_awst
        on bom_observation (date_trunc('month', observation_time at time zone 'AWST'), station_id)"""
    )
    op.execute(
        """create index if not exists
            idx_bom_observation_day_aest
        on bom_observation (date_trunc('day', observation_time at time zone 'AEST'), station_id)"""
    )
    op.execute(
        """create index if not exists
            idx_bom_observation_day_awst
        on bom_observation (date_trunc('day', observation_time at time zone 'AWST'), station_id)"""
    )


def downgrade() -> None:
    op.execute("drop index if exists idx_bom_observation_month_aest")
    op.execute("drop index if exists idx_bom_observation_month_awst")
    op.execute("drop index if exists idx_bom_observation_day_aest")
    op.execute("drop index if exists idx_bom_observation_day_awst")
