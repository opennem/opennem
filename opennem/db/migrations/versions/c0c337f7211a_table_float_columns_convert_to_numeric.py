# pylint: disable=no-member
"""
table float columns convert to numeric

Revision ID: c0c337f7211a
Revises: 67cc493a27d4
Create Date: 2024-12-28 16:03:04.266169

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c0c337f7211a'
down_revision = '67cc493a27d4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Units table
    op.alter_column('units', 'unit_capacity',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=20, scale=6),
               existing_nullable=True)
    op.alter_column('units', 'emissions_factor_co2',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=20, scale=6),
               existing_nullable=True)

    # Facility Scada table
    op.alter_column('facility_scada', 'generated',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=20, scale=6),
               existing_nullable=True)
    op.alter_column('facility_scada', 'energy',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               type_=sa.Numeric(precision=20, scale=6),
               existing_nullable=True)

    # Balancing Summary table
    # op.alter_column('balancing_summary', 'forecast_load',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('balancing_summary', 'generation_scheduled',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('balancing_summary', 'generation_non_scheduled',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('balancing_summary', 'generation_total',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('balancing_summary', 'net_interchange',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('balancing_summary', 'demand',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('balancing_summary', 'demand_total',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('balancing_summary', 'price',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('balancing_summary', 'price_dispatch',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('balancing_summary', 'net_interchange_trading',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)

    # Facility Aggregate table
    # op.alter_column('at_facility_intervals', 'generated',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('at_facility_intervals', 'energy',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('at_facility_intervals', 'emissions',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('at_facility_intervals', 'emissions_intensity',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)
    # op.alter_column('at_facility_intervals', 'market_value',
    #            existing_type=sa.DOUBLE_PRECISION(precision=53),
    #            type_=sa.Numeric(precision=20, scale=6),
    #            existing_nullable=True)


def downgrade() -> None:
    # Facility Aggregate table
    # op.alter_column('at_facility_intervals', 'market_value',
    #            existing_type=sa.Numeric(precision=20, scale=6),
    #            type_=sa.DOUBLE_PRECISION(precision=53),
    #            existing_nullable=True)
    # op.alter_column('at_facility_intervals', 'emissions_intensity',
    #            existing_type=sa.Numeric(precision=20, scale=6),
    #            type_=sa.DOUBLE_PRECISION(precision=53),
    #            existing_nullable=True)
    # op.alter_column('at_facility_intervals', 'emissions',
    #            existing_type=sa.Numeric(precision=20, scale=6),
    #            type_=sa.DOUBLE_PRECISION(precision=53),
    #            existing_nullable=True)
    # op.alter_column('at_facility_intervals', 'energy',
    #            existing_type=sa.Numeric(precision=20, scale=6),
    #            type_=sa.DOUBLE_PRECISION(precision=53),
    #            existing_nullable=True)
    # op.alter_column('at_facility_intervals', 'generated',
    #            existing_type=sa.Numeric(precision=20, scale=6),
    #            type_=sa.DOUBLE_PRECISION(precision=53),
    #            existing_nullable=True)

    # Balancing Summary table
    op.alter_column('balancing_summary', 'net_interchange_trading',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('balancing_summary', 'price_dispatch',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('balancing_summary', 'price',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('balancing_summary', 'demand_total',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('balancing_summary', 'demand',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('balancing_summary', 'net_interchange',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('balancing_summary', 'generation_total',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('balancing_summary', 'generation_non_scheduled',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('balancing_summary', 'generation_scheduled',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('balancing_summary', 'forecast_load',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)

    # Facility Scada table
    op.alter_column('facility_scada', 'energy',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('facility_scada', 'generated',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)

    # Units table
    op.alter_column('units', 'emissions_factor_co2',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
    op.alter_column('units', 'unit_capacity',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.DOUBLE_PRECISION(precision=53),
               existing_nullable=True)
