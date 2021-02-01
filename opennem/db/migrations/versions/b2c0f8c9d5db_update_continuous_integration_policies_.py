# pylint: disable=no-member
"""
Update continuous integration policies for mv_facility_energy_hour

Revision ID: b2c0f8c9d5db
Revises: 60ff840c16c5
Create Date: 2021-02-02 02:09:35.724514

"""
from alembic import op
from sqlalchemy.exc import ProgrammingError

# revision identifiers, used by Alembic.
revision = "b2c0f8c9d5db"
down_revision = "60ff840c16c5"
branch_labels = None
depends_on = None

VIEWS = [
    {
        "name": "mv_facility_energy_hour",
        "interval": "30 minutes",
        "start_offset": "6 hours",
        "end_offset": "1 hour",
    },
]

query_drop = "SELECT remove_continuous_aggregate_policy('{view_name}')"

query_create = """SELECT add_continuous_aggregate_policy('{view_name}',
    start_offset => INTERVAL '{start_offset}',
    end_offset => '{end_offset}',
    schedule_interval => INTERVAL '{schedule_size}');
"""


def upgrade() -> None:
    for v in VIEWS:
        q_drop = query_drop.format(view_name=v["name"])
        q_create = query_create.format(
            view_name=v["name"],
            schedule_size=v["interval"],
            start_offset=v["start_offset"],
            end_offset=v["end_offset"],
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
