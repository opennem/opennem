"""Drop unused indexes on balancing_summary and at_network_flows

- idx_balancing_price_lookup: partial index, zero scans
- idx_at_network_flows_network_id_trading_interval: duplicate of PK prefix
- idx_at_network_flows_trading_interval_facility_code: duplicate of PK columns

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-03-23
"""

from alembic import op

revision = "c4d5e6f7a8b9"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None

_DROP = [
    "idx_balancing_price_lookup",
    "idx_at_network_flows_network_id_trading_interval",
    "idx_at_network_flows_trading_interval_facility_code",
]


def upgrade() -> None:
    for idx in _DROP:
        op.execute(f"DROP INDEX IF EXISTS {idx}")


def downgrade() -> None:
    op.execute(
        "CREATE INDEX idx_balancing_price_lookup "
        "ON public.balancing_summary USING btree (interval, network_id, network_region, price) "
        "WHERE (is_forecast = false AND price IS NOT NULL)"
    )
    op.execute(
        "CREATE INDEX idx_at_network_flows_network_id_trading_interval "
        "ON public.at_network_flows USING btree (network_id, interval)"
    )
    op.execute(
        "CREATE INDEX idx_at_network_flows_trading_interval_facility_code "
        "ON public.at_network_flows USING btree (interval, network_id, network_region)"
    )
