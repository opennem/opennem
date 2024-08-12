# pylint: disable=no-member
"""
index facility_scada balancing_summary

Revision ID: 99d1cadc9655
Revises: cbdfea6ca557
Create Date: 2024-08-12 11:10:56.013492

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "99d1cadc9655"
down_revision = "cbdfea6ca557"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("idx_balancing_summary_network_region_interval", table_name="balancing_summary")

    op.create_index(
        "idx_balancing_summary_interval_network_region",
        "balancing_summary",
        ["interval", "network_id", "network_region"],
        unique=False,
        postgresql_ops={"interval": "DESC"},
    )

    op.create_index(
        "idx_facility_scada_interval_network",
        "facility_scada",
        ["interval", "network_id"],
        unique=False,
        postgresql_ops={"interval": "DESC"},
    )
    op.create_index(op.f("ix_facility_scada_facility_code"), "facility_scada", ["facility_code"], unique=False)
    op.create_index(op.f("ix_facility_scada_interval"), "facility_scada", ["interval"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_facility_scada_interval"), table_name="facility_scada")
    op.drop_index(op.f("ix_facility_scada_facility_code"), table_name="facility_scada")
    op.drop_index(
        "idx_facility_scada_interval_network", table_name="facility_scada", postgresql_ops={"interval": "DESC"}
    )
    op.drop_index("idx_facility_scada_facility_code_interval", table_name="facility_scada", postgresql_using="btree")
    op.create_index(
        "idx_facility_scada_facility_code_interval",
        "facility_scada",
        ["facility_code", sa.text("interval DESC")],
        unique=False,
    )
    op.create_index("facility_scada_new_interval_idx", "facility_scada", [sa.text("interval DESC")], unique=False)
    op.alter_column("bom_station", "priority", existing_type=sa.INTEGER(), nullable=True)
    op.drop_index(
        "idx_balancing_summary_interval_network_region",
        table_name="balancing_summary",
        postgresql_ops={"interval": "DESC"},
    )
    op.drop_index(
        "idx_balancing_summary_network_region_interval", table_name="balancing_summary", postgresql_using="btree"
    )
    op.create_index(
        "idx_balancing_summary_network_region_interval",
        "balancing_summary",
        ["network_region", sa.text("interval DESC")],
        unique=False,
    )
    op.drop_index(
        "idx_balancing_summary_network_id_interval", table_name="balancing_summary", postgresql_using="btree"
    )
    op.create_index(
        "idx_balancing_summary_network_id_interval",
        "balancing_summary",
        ["network_id", sa.text("interval DESC")],
        unique=False,
    )
    op.create_index(
        "balancing_summary_new_interval_idx", "balancing_summary", [sa.text("interval DESC")], unique=False
    )
    op.drop_index(
        "idx_at_network_flowsy_v3_network_id_trading_interval",
        table_name="at_network_flows_v3",
        postgresql_using="btree",
    )
    op.create_index(
        "idx_at_network_flowsy_v3_network_id_trading_interval",
        "at_network_flows_v3",
        ["network_id", sa.text("trading_interval DESC")],
        unique=False,
    )
    op.drop_index(
        "idx_at_network_flowsy_network_id_trading_interval", table_name="at_network_flows", postgresql_using="btree"
    )
    op.create_index(
        "idx_at_network_flowsy_network_id_trading_interval",
        "at_network_flows",
        ["network_id", sa.text("trading_interval DESC")],
        unique=False,
    )
    op.drop_index(
        "idx_at_network_demand_network_id_trading_interval", table_name="at_network_demand", postgresql_using="btree"
    )
    op.create_index(
        "idx_at_network_demand_network_id_trading_interval",
        "at_network_demand",
        ["network_id", sa.text("trading_day DESC")],
        unique=False,
    )
    op.drop_index(
        "idx_at_facility_day_facility_code_trading_interval", table_name="at_facility_daily", postgresql_using="btree"
    )
    op.create_index(
        "idx_at_facility_day_facility_code_trading_interval",
        "at_facility_daily",
        ["facility_code", sa.text("trading_day DESC")],
        unique=False,
    )
    op.drop_index(
        "idx_at_facility_daily_network_id_trading_interval", table_name="at_facility_daily", postgresql_using="btree"
    )
    op.create_index(
        "idx_at_facility_daily_network_id_trading_interval",
        "at_facility_daily",
        ["network_id", sa.text("trading_day DESC")],
        unique=False,
    )
