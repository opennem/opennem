# pylint: disable=no-member
"""
Remove old interconnect facilities and stations

Revision ID: 8746bdb27550
Revises: 6767d0102992
Create Date: 2020-12-24 14:56:00.999511

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "8746bdb27550"
down_revision = "6767d0102992"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "delete from station where id in (select distinct station_id from facility where fueltech_id in ('imports', 'exports'))"
    )


def downgrade() -> None:
    pass
