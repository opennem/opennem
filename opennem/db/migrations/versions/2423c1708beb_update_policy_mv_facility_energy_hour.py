# pylint: disable=no-member
"""
Update policy mv_facility_energy_hour

Revision ID: 2423c1708beb
Revises: 7af7a611233f
Create Date: 2021-01-26 02:19:03.245419

"""
from alembic import op
from sqlalchemy.exc import ProgrammingError

# revision identifiers, used by Alembic.
revision = "2423c1708beb"
down_revision = "7af7a611233f"
branch_labels = None
depends_on = None


VIEWS = [
    {"name": "mv_facility_energy_hour", "interval": "30 minutes", "start_offset": "2 hours"},
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
