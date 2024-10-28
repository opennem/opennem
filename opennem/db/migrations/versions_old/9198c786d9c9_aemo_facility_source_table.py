# pylint: disable=no-member
"""
aemo facility source table

Revision ID: 9198c786d9c9
Revises: 2408ca24684c
Create Date: 2023-03-14 17:27:02.536783

"""
import sqlalchemy as sa
from alembic import op

revision = "9198c786d9c9"
down_revision = "2408ca24684c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "aemo_facility_data",
        sa.Column(
            "aemo_source",
            sa.Enum("rel", "gi", name="aemodatasource"),
            nullable=False,
        ),
        sa.Column("source_date", sa.Date(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("name_network", sa.Text(), nullable=True),
        sa.Column("network_region", sa.Text(), nullable=True),
        sa.Column("fueltech_id", sa.Text(), nullable=True),
        sa.Column("status_id", sa.Text(), nullable=True),
        sa.Column("duid", sa.Text(), nullable=True),
        sa.Column("units_no", sa.Integer(), nullable=True),
        sa.Column("capacity_registered", sa.Numeric(), nullable=True),
        sa.Column("closure_year_expected", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("aemo_source", "source_date"),
    )
    op.create_index(
        "idx_facility_scada_trading_interval_facility_code",
        "facility_scada",
        ["trading_interval", "facility_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_facility_scada_trading_interval_facility_code",
        table_name="facility_scada",
    )
    op.drop_table("aemo_facility_data")
