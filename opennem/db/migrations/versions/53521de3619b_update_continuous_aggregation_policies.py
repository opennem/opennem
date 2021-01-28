# pylint: disable=no-member
"""
Update continuous aggregation policies

Revision ID: 53521de3619b
Revises: d13c12e02b4e
Create Date: 2021-01-28 18:19:31.385069

"""
from alembic import op
from sqlalchemy.exc import ProgrammingError

# revision identifiers, used by Alembic.
revision = "53521de3619b"
down_revision = "d13c12e02b4e"
branch_labels = None
depends_on = None


VIEWS = [
    {"name": "mv_facility_energy_hour", "interval": "5 minutes", "start_offset": "6 hours"},
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
