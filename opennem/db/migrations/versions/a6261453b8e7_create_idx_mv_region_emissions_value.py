# pylint: disable=no-member
"""
create idx_mv_region_emissions_value

Revision ID: a6261453b8e7
Revises: c203c9207aa3
Create Date: 2021-01-29 02:12:58.397189

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "a6261453b8e7"
down_revision = "c203c9207aa3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_region_emissions_unique ON mv_region_emissions (trading_interval, network_region);"
    )


def downgrade() -> None:
    op.execute("drop index if exists idx_mv_region_emissions_unique")
