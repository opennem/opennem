# pylint: disable=no-member
"""
at_network_fueltech_intervals table

Revision ID: 0cabef36e666
Revises: a2683a564e2a
Create Date: 2022-10-25 15:34:26.278260

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0cabef36e666"
down_revision = "a2683a564e2a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "at_network_fueltech_intervals",
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "trading_interval",
            postgresql.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column("network_id", sa.Text(), nullable=False),
        sa.Column("network_region", sa.Text(), nullable=False),
        sa.Column("fueltech_id", sa.Text(), nullable=False),
        sa.Column("generated", sa.Numeric(), nullable=True),
        sa.Column("energy", sa.Numeric(), nullable=True),
        sa.Column("market_value", sa.Numeric(), nullable=True),
        sa.Column("emissions", sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(
            ["network_id"],
            ["network.code"],
            name="fk_at_network_fueltech_intervals_network_code",
        ),
        sa.PrimaryKeyConstraint("trading_interval", "network_id", "network_region", "fueltech_id"),
    )
    op.create_index(
        "idx_at_network_fueltech_intervals_network_id_interval",
        "at_network_fueltech_intervals",
        ["network_id", sa.text("trading_interval DESC")],
        unique=False,
    )
    op.create_index(
        "idx_at_network_fueltech_intervals_network_interval_fuel_rgn",
        "at_network_fueltech_intervals",
        ["trading_interval", "network_id", "network_region", "fueltech_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_at_network_fueltech_intervals_network_id"),
        "at_network_fueltech_intervals",
        ["network_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_at_network_fueltech_intervals_network_region"),
        "at_network_fueltech_intervals",
        ["network_region"],
        unique=False,
    )
    op.create_index(
        op.f("ix_at_network_fueltech_intervals_trading_interval"),
        "at_network_fueltech_intervals",
        ["trading_interval"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_at_network_fueltech_intervals_trading_interval"),
        table_name="at_network_fueltech_intervals",
    )
    op.drop_index(
        op.f("ix_at_network_fueltech_intervals_network_region"),
        table_name="at_network_fueltech_intervals",
    )
    op.drop_index(
        op.f("ix_at_network_fueltech_intervals_network_id"),
        table_name="at_network_fueltech_intervals",
    )
    op.drop_index(
        "idx_at_network_fueltech_intervals_network_interval_fuel_rgn",
        table_name="at_network_fueltech_intervals",
    )
    op.drop_index(
        "idx_at_network_fueltech_intervals_network_id_interval",
        table_name="at_network_fueltech_intervals",
    )
    op.drop_table("at_network_fueltech_intervals")
