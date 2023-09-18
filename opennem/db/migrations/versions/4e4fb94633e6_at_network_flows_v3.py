# pylint: disable=no-member
"""
at_network_flows_v3

Revision ID: 4e4fb94633e6
Revises: 60f042e69758
Create Date: 2023-09-19 06:26:19.563734

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "4e4fb94633e6"
down_revision = "60f042e69758"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "at_network_flows_v3",
        sa.Column(
            "trading_interval",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column("network_id", sa.Text(), nullable=False),
        sa.Column("network_region", sa.Text(), nullable=False),
        sa.Column("energy_imports", sa.Numeric(), nullable=True),
        sa.Column("energy_exports", sa.Numeric(), nullable=True),
        sa.Column("market_value_imports", sa.Numeric(), nullable=True),
        sa.Column("market_value_exports", sa.Numeric(), nullable=True),
        sa.Column("emissions_imports", sa.Numeric(), nullable=True),
        sa.Column("emissions_exports", sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(
            ["network_id"],
            ["network.code"],
            name="fk_at_network_flows_network_code",
        ),
        sa.PrimaryKeyConstraint("trading_interval", "network_id", "network_region"),
    )
    op.create_index(
        "idx_at_network_flows_v3_trading_interval_facility_code",
        "at_network_flows_v3",
        ["trading_interval", "network_id", "network_region"],
        unique=False,
    )
    op.create_index(
        "idx_at_network_flowsy_v3_network_id_trading_interval",
        "at_network_flows_v3",
        ["network_id", sa.text("trading_interval DESC")],
        unique=False,
    )
    op.create_index(
        op.f("ix_at_network_flows_v3_network_id"),
        "at_network_flows_v3",
        ["network_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_at_network_flows_v3_network_region"),
        "at_network_flows_v3",
        ["network_region"],
        unique=False,
    )
    op.create_index(
        op.f("ix_at_network_flows_v3_trading_interval"),
        "at_network_flows_v3",
        ["trading_interval"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_at_network_flows_v3_trading_interval"),
        table_name="at_network_flows_v3",
    )
    op.drop_index(
        op.f("ix_at_network_flows_v3_network_region"),
        table_name="at_network_flows_v3",
    )
    op.drop_index(
        op.f("ix_at_network_flows_v3_network_id"),
        table_name="at_network_flows_v3",
    )
    op.drop_index(
        "idx_at_network_flowsy_v3_network_id_trading_interval",
        table_name="at_network_flows_v3",
    )
    op.drop_index(
        "idx_at_network_flows_v3_trading_interval_facility_code",
        table_name="at_network_flows_v3",
    )
    op.drop_table("at_network_flows_v3")
