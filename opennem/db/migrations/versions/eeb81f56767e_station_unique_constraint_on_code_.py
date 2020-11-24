# pylint: disable=no-member
"""
facility + station unique constraint on code + network

Revision ID: eeb81f56767e
Revises: 4bf86ff5c8ff
Create Date: 2020-11-24 11:03:42.278896

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "eeb81f56767e"
down_revision = "4bf86ff5c8ff"
branch_labels = None
depends_on = None


def upgrade():
    # clean up stations + facilities from dupe bug
    op.execute(
        "delete from facility where id not in (select min(id) from facility group by network_id, code)"
    )
    op.execute("delete from facility where approved is false")
    op.execute(
        "delete from station where id not in (select min(id) from station group by code)"
    )

    # facility table
    op.alter_column("facility", "code", nullable=False)
    op.create_unique_constraint(
        "excl_facility_network_id_code", "facility", ["network_id", "code"]
    )

    # station table constraints
    op.alter_column("station", "code", nullable=False)
    op.create_unique_constraint(
        "excl_station_network_duid", "station", ["code"]
    )


def downgrade():
    op.alter_column("facility", "code", nullable=True)
    op.drop_constraint("excl_facility_network_id_code")

    op.alter_column("station", "code", nullable=True)
    op.drop_constraint("excl_station_network_duid")
