# pylint: disable=no-member
"""
Update policy mv_nem_facility_power_5min

Revision ID: f7e87ce05302
Revises: 99a6fee86d14
Create Date: 2021-01-26 01:59:53.604797

"""
from alembic import op
from sqlalchemy.exc import ProgrammingError

# revision identifiers, used by Alembic.
revision = "f7e87ce05302"
down_revision = "99a6fee86d14"
branch_labels = None
depends_on = None

VIEWS = [
    {"name": "mv_nem_facility_power_5min", "interval": "5 minutes", "start_offset": "2 hours"},
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
