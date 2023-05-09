# pylint: disable=no-member
"""
at_facility_daily facility code index

Revision ID: 40b7b3ffb0cc
Revises: 35baeb0b92c9
Create Date: 2023-05-09 13:30:50.686745

"""
from alembic import op

revision = "40b7b3ffb0cc"
down_revision = "35baeb0b92c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_at_facility_daily_network_id", table_name="at_facility_daily")
    op.drop_index("ix_at_facility_daily_network_region", table_name="at_facility_daily")
    op.create_index(
        "idx_at_facility_daily_facility_code_network_id_trading_day",
        "at_facility_daily",
        ["network_id", "facility_code", "trading_day"],
        unique=True,
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index(
        "idx_at_facility_daily_facility_code_network_id_trading_day",
        table_name="at_facility_daily",
        postgresql_using="btree",
    )
    op.create_index(
        "ix_at_facility_daily_network_region",
        "at_facility_daily",
        ["network_region"],
        unique=False,
    )
    op.create_index(
        "ix_at_facility_daily_network_id",
        "at_facility_daily",
        ["network_id"],
        unique=False,
    )
