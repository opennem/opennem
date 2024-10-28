# pylint: disable=no-member
"""
Facility daily aggregate table

Revision ID: c55917f188a5
Revises: 87043aacf46a
Create Date: 2021-04-10 12:46:08.713070

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c55917f188a5"
down_revision = "87043aacf46a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "at_facility_daily",
        sa.Column("trading_day", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("network_id", sa.Text(), nullable=False),
        sa.Column("facility_code", sa.Text(), nullable=False),
        sa.Column("fueltech_id", sa.Text(), nullable=True),
        sa.Column("energy", sa.Numeric(), nullable=True),
        sa.Column("market_value", sa.Numeric(), nullable=True),
        sa.Column("emissions", sa.Numeric(), nullable=True),
        sa.ForeignKeyConstraint(
            ["facility_code"],
            ["facility.code"],
            name="fk_at_facility_daily_facility_code",
        ),
        sa.ForeignKeyConstraint(
            ["network_id"],
            ["network.code"],
            name="fk_at_facility_daily_network_code",
        ),
        sa.PrimaryKeyConstraint("trading_day", "network_id", "facility_code"),
    )
    op.create_index(
        "idx_at_facility_daily_network_id_trading_interval",
        "at_facility_daily",
        ["network_id", sa.text("trading_day DESC")],
        unique=False,
    )
    op.create_index(
        "idx_at_facility_daily_trading_interval_facility_code",
        "at_facility_daily",
        ["trading_day", "facility_code"],
        unique=False,
    )
    op.create_index(
        "idx_at_facility_day_facility_code_trading_interval",
        "at_facility_daily",
        ["facility_code", sa.text("trading_day DESC")],
        unique=False,
    )
    op.create_index(
        op.f("ix_at_facility_daily_facility_code"),
        "at_facility_daily",
        ["facility_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_at_facility_daily_network_id"),
        "at_facility_daily",
        ["network_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_at_facility_daily_trading_day"),
        "at_facility_daily",
        ["trading_day"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_at_facility_daily_trading_day"),
        table_name="at_facility_daily",
    )
    op.drop_index(op.f("ix_at_facility_daily_network_id"), table_name="at_facility_daily")
    op.drop_index(
        op.f("ix_at_facility_daily_facility_code"),
        table_name="at_facility_daily",
    )
    op.drop_index(
        "idx_at_facility_day_facility_code_trading_interval",
        table_name="at_facility_daily",
    )
    op.drop_index(
        "idx_at_facility_daily_trading_interval_facility_code",
        table_name="at_facility_daily",
    )
    op.drop_index(
        "idx_at_facility_daily_network_id_trading_interval",
        table_name="at_facility_daily",
    )
    op.drop_table("at_facility_daily")
