# pylint: disable=no-member
"""
remove at_network_flows_v3 table

Revision ID: 0917d7d2ae72
Revises: a3fa44a8bf4d
Create Date: 2024-01-25 18:27:11.038534

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0917d7d2ae72"
down_revision = "a3fa44a8bf4d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "idx_at_network_flows_v3_trading_interval_facility_code",
        table_name="at_network_flows_v3",
    )
    op.drop_index(
        "idx_at_network_flowsy_v3_network_id_trading_interval",
        table_name="at_network_flows_v3",
    )
    op.drop_index("ix_at_network_flows_v3_network_id", table_name="at_network_flows_v3")
    op.drop_index(
        "ix_at_network_flows_v3_network_region",
        table_name="at_network_flows_v3",
    )
    op.drop_index(
        "ix_at_network_flows_v3_trading_interval",
        table_name="at_network_flows_v3",
    )
    op.drop_table("at_network_flows_v3")


def downgrade() -> None:
    op.create_table(
        "at_network_flows_v3",
        sa.Column(
            "trading_interval",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("network_id", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("network_region", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("energy_imports", sa.NUMERIC(), autoincrement=False, nullable=True),
        sa.Column("energy_exports", sa.NUMERIC(), autoincrement=False, nullable=True),
        sa.Column(
            "market_value_imports",
            sa.NUMERIC(),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "market_value_exports",
            sa.NUMERIC(),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "emissions_imports",
            sa.NUMERIC(),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "emissions_exports",
            sa.NUMERIC(),
            autoincrement=False,
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["network_id"],
            ["network.code"],
            name="fk_at_network_flows_network_code",
        ),
        sa.PrimaryKeyConstraint(
            "trading_interval",
            "network_id",
            "network_region",
            name="at_network_flows_v3_pkey",
        ),
    )
    op.create_index(
        "ix_at_network_flows_v3_trading_interval",
        "at_network_flows_v3",
        ["trading_interval"],
        unique=False,
    )
    op.create_index(
        "ix_at_network_flows_v3_network_region",
        "at_network_flows_v3",
        ["network_region"],
        unique=False,
    )
    op.create_index(
        "ix_at_network_flows_v3_network_id",
        "at_network_flows_v3",
        ["network_id"],
        unique=False,
    )
    op.create_index(
        "idx_at_network_flowsy_v3_network_id_trading_interval",
        "at_network_flows_v3",
        ["network_id", sa.text("trading_interval DESC")],
        unique=False,
    )
    op.create_index(
        "idx_at_network_flows_v3_trading_interval_facility_code",
        "at_network_flows_v3",
        ["trading_interval", "network_id", "network_region"],
        unique=False,
    )
