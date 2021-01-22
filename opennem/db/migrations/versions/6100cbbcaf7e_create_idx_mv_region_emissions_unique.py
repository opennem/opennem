# pylint: disable=no-member
"""
create idx_mv_region_emissions_unique

Revision ID: 6100cbbcaf7e
Revises: 297112c824d0
Create Date: 2021-01-22 16:15:38.204480

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "6100cbbcaf7e"
down_revision = "297112c824d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_region_emissions_unique ON mv_region_emissions (trading_interval, network_region);"
    )


def downgrade() -> None:
    op.execute("drop index if exists idx_mv_region_emissions_unique")
