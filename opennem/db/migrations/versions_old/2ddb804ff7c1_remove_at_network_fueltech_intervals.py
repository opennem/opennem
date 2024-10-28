# pylint: disable=no-member
"""
remove at_network_fueltech_intervals

Revision ID: 2ddb804ff7c1
Revises: 1686c3029774
Create Date: 2023-03-28 16:43:08.980974

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "2ddb804ff7c1"
down_revision = "1686c3029774"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "idx_at_network_fueltech_intervals_network_id_interval",
        table_name="at_network_fueltech_intervals",
    )
    op.drop_index(
        "idx_at_network_fueltech_intervals_network_interval_fuel_rgn",
        table_name="at_network_fueltech_intervals",
    )
    op.drop_index(
        "ix_at_network_fueltech_intervals_network_id",
        table_name="at_network_fueltech_intervals",
    )
    op.drop_index(
        "ix_at_network_fueltech_intervals_network_region",
        table_name="at_network_fueltech_intervals",
    )
    op.drop_index(
        "ix_at_network_fueltech_intervals_trading_interval",
        table_name="at_network_fueltech_intervals",
    )
    op.drop_table("at_network_fueltech_intervals")


def downgrade() -> None:
    op.create_table(
        "at_network_fueltech_intervals",
        sa.Column("created_by", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column(
            "trading_interval",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column("network_id", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("network_region", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("fueltech_id", sa.TEXT(), autoincrement=False, nullable=False),
        sa.Column("generated", sa.NUMERIC(), autoincrement=False, nullable=True),
        sa.Column("energy", sa.NUMERIC(), autoincrement=False, nullable=True),
        sa.Column("market_value", sa.NUMERIC(), autoincrement=False, nullable=True),
        sa.Column("emissions", sa.NUMERIC(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["network_id"],
            ["network.code"],
            name="fk_at_network_fueltech_intervals_network_code",
        ),
        sa.PrimaryKeyConstraint(
            "trading_interval",
            "network_id",
            "network_region",
            "fueltech_id",
            name="at_network_fueltech_intervals_pkey",
        ),
    )
    op.create_index(
        "ix_at_network_fueltech_intervals_trading_interval",
        "at_network_fueltech_intervals",
        ["trading_interval"],
        unique=False,
    )
    op.create_index(
        "ix_at_network_fueltech_intervals_network_region",
        "at_network_fueltech_intervals",
        ["network_region"],
        unique=False,
    )
    op.create_index(
        "ix_at_network_fueltech_intervals_network_id",
        "at_network_fueltech_intervals",
        ["network_id"],
        unique=False,
    )
    op.create_index(
        "idx_at_network_fueltech_intervals_network_interval_fuel_rgn",
        "at_network_fueltech_intervals",
        ["trading_interval", "network_id", "network_region", "fueltech_id"],
        unique=False,
    )
    op.create_index(
        "idx_at_network_fueltech_intervals_network_id_interval",
        "at_network_fueltech_intervals",
        ["network_id", "trading_interval"],
        unique=False,
    )
