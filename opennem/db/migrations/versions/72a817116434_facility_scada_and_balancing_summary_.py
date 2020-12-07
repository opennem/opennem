# pylint: disable=no-member
"""
Facility Scada and Balancing Summary facility and network indicies

Revision ID: 72a817116434
Revises: 467a3223b204
Create Date: 2020-12-07 23:57:33.383834

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "72a817116434"
down_revision = "467a3223b204"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "create index if not exists idx_facility_scada_facility_code_trading_interval on facility_scada (facility_code, trading_interval desc)"
    )

    op.execute(
        "create index if not exists idx_facility_scada_network_id_trading_interval on facility_scada (network_id, trading_interval desc)"
    )

    op.execute(
        "create index if not exists idx_balancing_summary_network_id_trading_interval on balancing_summary (network_id, trading_interval desc)"
    )

    op.execute(
        "create index if not exists idx_balancing_summary_network_region_trading_interval on balancing_summary (network_region, trading_interval desc);"
    )


def downgrade() -> None:
    op.execute(
        "drop index if exists idx_facility_scada_facility_code_trading_interval"
    )
    op.execute(
        "drop index if exists idx_facility_scada_network_id_trading_interval"
    )
    op.execute(
        "drop index if exists idx_balancing_summary_network_id_trading_interval"
    )
    op.execute(
        "drop index if exists idx_balancing_summary_network_region_trading_interval"
    )
