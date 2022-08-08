# pylint: disable=no-member
"""
aggregate network demand table

Revision ID: f6f4398975ed
Revises: e098f4d2a149
Create Date: 2022-08-08 05:53:02.256384

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "f6f4398975ed"
down_revision = "e098f4d2a149"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "at_network_demand",
        sa.Column("trading_day", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("network_id", sa.Text(), nullable=False),
        sa.Column("network_region", sa.Text(), nullable=False),
        sa.Column("demand_energy", sa.Numeric(), nullable=True),
        sa.Column("demand_market_value", sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(
            ["network_id"],
            ["network.code"],
            name="fk_at_facility_daily_network_code",
        ),
        sa.PrimaryKeyConstraint("trading_day", "network_id", "network_region"),
    )
    op.create_index(
        "idx_at_network_demand_network_id_trading_interval",
        "at_network_demand",
        ["network_id", sa.text("trading_day DESC")],
        unique=False,
    )
    op.create_index(
        "idx_at_network_demand_trading_interval_network_region",
        "at_network_demand",
        ["trading_day", "network_id", "network_region"],
        unique=False,
    )
    op.create_index(
        op.f("ix_at_network_demand_network_id"),
        "at_network_demand",
        ["network_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_at_network_demand_trading_day"),
        "at_network_demand",
        ["trading_day"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_at_network_demand_trading_day"),
        table_name="at_network_demand",
    )
    op.drop_index(op.f("ix_at_network_demand_network_id"), table_name="at_network_demand")
    op.drop_index(
        "idx_at_network_demand_trading_interval_network_region",
        table_name="at_network_demand",
    )
    op.drop_index(
        "idx_at_network_demand_network_id_trading_interval",
        table_name="at_network_demand",
    )
    op.drop_table("at_network_demand")
