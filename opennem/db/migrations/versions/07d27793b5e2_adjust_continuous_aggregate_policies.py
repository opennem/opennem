# pylint: disable=no-member
"""
Adjust continuous aggregate policies

Revision ID: 07d27793b5e2
Revises: 4a0f8c654257
Create Date: 2021-01-24 07:43:38.747557

"""
from alembic import op
from sqlalchemy.exc import ProgrammingError

# revision identifiers, used by Alembic.
revision = "07d27793b5e2"
down_revision = "4a0f8c654257"
branch_labels = None
depends_on = None


VIEWS = [
    {"name": "mv_nem_facility_power_5min", "interval": "30 minutes", "start_offset": "2 hours"},
    {"name": "mv_wem_facility_power_30min", "interval": "30 minutes", "start_offset": "2 hours"},
    {
        "name": "mv_interchange_power_nem_region",
        "interval": "30 minutes",
        "start_offset": "2 hours",
    },
    {
        "name": "mv_interchange_energy_nem_region",
        "interval": "30 minutes",
        "start_offset": "2 hours",
    },
    {"name": "mv_facility_energy_hour", "interval": "30 minutes", "start_offset": "2 hours"},
    {
        "name": "mv_balancing_summary_region_hour",
        "interval": "30 minutes",
        "start_offset": "2 hours",
    },
]

query_drop = "SELECT remove_continuous_aggregate_policy('{view_name}')"

query_create = """SELECT add_continuous_aggregate_policy('{view_name}',
    start_offset => INTERVAL '{start_offset}',
    end_offset => NULL,
    schedule_interval => INTERVAL '{schedule_size}');
"""


def upgrade() -> None:
    for v in VIEWS:
        q_drop = query_drop.format(view_name=v["name"])
        q_create = query_create.format(
            view_name=v["name"], schedule_size=v["interval"], start_offset=v["start_offset"]
        )

        with op.get_context().autocommit_block():
            try:
                op.execute(q_drop)
            except ProgrammingError:
                pass

        with op.get_context().autocommit_block():
            op.execute(q_create)


def downgrade() -> None:
    pass
