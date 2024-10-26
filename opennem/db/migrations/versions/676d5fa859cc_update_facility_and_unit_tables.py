# pylint: disable=no-member
"""
update facility and unit tables

Revision ID: 676d5fa859cc
Revises: 6ae9eb81dc08
Create Date: 2024-11-07 13:35:13.404088

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '676d5fa859cc'
down_revision = '6ae9eb81dc08'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('idx_balancing_summary_interval_network_region', table_name='balancing_summary')
    op.create_index('idx_balancing_summary_interval_network_region', 'balancing_summary', ['interval', 'network_id', 'network_region'], unique=False, postgresql_ops={'interval': 'DESC'})
    op.drop_index('ix_station_code', table_name='facilities')
    op.create_index(op.f('ix_facilities_code'), 'facilities', ['code'], unique=True)
    op.drop_constraint('fk_station_network_code', 'facilities', type_='foreignkey')
    op.drop_index('facility_scada_new_interval_idx', table_name='facility_scada')
    op.create_index('facility_scada_new_interval_idx', 'facility_scada', ['interval'], unique=False, postgresql_ops={'interval': 'DESC'})
    op.drop_index('idx_facility_scada_interval_network', table_name='facility_scada')
    op.create_index('idx_facility_scada_interval_network', 'facility_scada', ['interval', 'network_id'], unique=False, postgresql_ops={'interval': 'DESC'})
    op.alter_column('units', 'interconnector',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.drop_index('ix_facility_code', table_name='units')
    op.drop_index('ix_facility_data_first_seen', table_name='units')
    op.drop_index('ix_facility_data_last_seen', table_name='units')
    op.drop_index('ix_facility_interconnector', table_name='units')
    op.drop_index('ix_facility_interconnector_region_from', table_name='units')
    op.drop_index('ix_facility_interconnector_region_to', table_name='units')
    op.create_index(op.f('ix_units_code'), 'units', ['code'], unique=True)
    op.create_index(op.f('ix_units_data_first_seen'), 'units', ['data_first_seen'], unique=False)
    op.create_index(op.f('ix_units_data_last_seen'), 'units', ['data_last_seen'], unique=False)
    op.create_index(op.f('ix_units_interconnector'), 'units', ['interconnector'], unique=False)
    op.create_index(op.f('ix_units_interconnector_region_from'), 'units', ['interconnector_region_from'], unique=False)
    op.create_index(op.f('ix_units_interconnector_region_to'), 'units', ['interconnector_region_to'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_units_interconnector_region_to'), table_name='units')
    op.drop_index(op.f('ix_units_interconnector_region_from'), table_name='units')
    op.drop_index(op.f('ix_units_interconnector'), table_name='units')
    op.drop_index(op.f('ix_units_data_last_seen'), table_name='units')
    op.drop_index(op.f('ix_units_data_first_seen'), table_name='units')
    op.drop_index(op.f('ix_units_code'), table_name='units')
    op.create_index('ix_facility_interconnector_region_to', 'units', ['interconnector_region_to'], unique=False)
    op.create_index('ix_facility_interconnector_region_from', 'units', ['interconnector_region_from'], unique=False)
    op.create_index('ix_facility_interconnector', 'units', ['interconnector'], unique=False)
    op.create_index('ix_facility_data_last_seen', 'units', ['data_last_seen'], unique=False)
    op.create_index('ix_facility_data_first_seen', 'units', ['data_first_seen'], unique=False)
    op.create_index('ix_facility_code', 'units', ['code'], unique=True)
    op.alter_column('units', 'interconnector',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.drop_index('idx_facility_scada_interval_network', table_name='facility_scada', postgresql_ops={'interval': 'DESC'})
    op.create_index('idx_facility_scada_interval_network', 'facility_scada', [sa.text('interval DESC'), 'network_id'], unique=False)
    op.drop_index('facility_scada_new_interval_idx', table_name='facility_scada', postgresql_ops={'interval': 'DESC'})
    op.create_index('facility_scada_new_interval_idx', 'facility_scada', [sa.text('interval DESC')], unique=False)
    op.create_foreign_key('fk_station_network_code', 'facilities', 'network', ['network_id'], ['code'])
    op.drop_index(op.f('ix_facilities_code'), table_name='facilities')
    op.create_index('ix_station_code', 'facilities', ['code'], unique=True)
    op.drop_index('idx_balancing_summary_interval_network_region', table_name='balancing_summary', postgresql_ops={'interval': 'DESC'})
    op.create_index('idx_balancing_summary_interval_network_region', 'balancing_summary', [sa.text('interval DESC'), 'network_id', 'network_region'], unique=False)
