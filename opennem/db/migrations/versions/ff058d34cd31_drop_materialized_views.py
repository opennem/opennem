# pylint: disable=no-member
"""
drop materialized views

Revision ID: ff058d34cd31
Revises: 8ab718cb9fde
Create Date: 2023-04-27 21:41:04.084573

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "ff058d34cd31"
down_revision = "8ab718cb9fde"
branch_labels = None
depends_on = None

VIEW_NAMES = [
    "mv_interchange_energy_nem_region",
    "mv_region_emissions",
    "mv_region_emissions_45d",
    "mv_facility_30m_all",
    "mv_facility_45d",
    "mv_facility_all",
]


def upgrade() -> None:
    for view_name in VIEW_NAMES:
        op.execute(f"drop materialized view if exists {view_name} cascade;")


def downgrade() -> None:
    pass
