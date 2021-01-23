# pylint: disable=no-member
"""
Set continous aggregate policies

Revision ID: 4a0f8c654257
Revises: 47b8cabac4bb
Create Date: 2021-01-23 18:57:00.102509

"""
from alembic import op
from sqlalchemy.exc import ProgrammingError

# revision identifiers, used by Alembic.
revision = "4a0f8c654257"
down_revision = "47b8cabac4bb"
branch_labels = None
depends_on = None

VIEWS = [
    {"name": "mv_nem_facility_power_5min", "interval": "5 minutes"},
    {"name": "mv_wem_facility_power_30min", "interval": "5 minutes"},
    {"name": "mv_interchange_power_nem_region", "interval": "5 minutes"},
    {"name": "mv_interchange_energy_nem_region", "interval": "5 minutes"},
    {"name": "mv_facility_energy_hour", "interval": "30 minutes"},
    {"name": "mv_balancing_summary_region_hour", "interval": "30 minutes"},
]

query_drop = "SELECT remove_continuous_aggregate_policy('{view_name}')"

query_create = """SELECT add_continuous_aggregate_policy('{view_name}',
    start_offset => INTERVAL '1 day',
    end_offset => NULL,
    schedule_interval => INTERVAL '{schedule_size}');
"""


def upgrade() -> None:
    for v in VIEWS:
        q_drop = query_drop.format(view_name=v["name"])
        q_create = query_create.format(view_name=v["name"], schedule_size=v["interval"])

        with op.get_context().autocommit_block():
            try:
                op.execute(q_drop)
            except ProgrammingError:
                pass

        with op.get_context().autocommit_block():
            op.execute(q_create)


def downgrade() -> None:
    pass
