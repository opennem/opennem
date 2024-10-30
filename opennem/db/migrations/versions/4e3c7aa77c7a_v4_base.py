# pylint: disable=no-member
"""
v4 base

Revision ID: 4e3c7aa77c7a
Revises: f1541d5d4008
Create Date: 2024-11-08 11:53:14.243623

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4e3c7aa77c7a'
down_revision = 'f1541d5d4008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('idx_at_network_demand_network_id_trading_interval', table_name='at_network_demand')
    op.create_index('idx_at_network_demand_network_id_trading_interval', 'at_network_demand', ['network_id', 'trading_day'], unique=False, postgresql_using='btree')
    op.drop_index('idx_at_network_flowsy_network_id_trading_interval', table_name='at_network_flows')
    op.create_index('idx_at_network_flowsy_network_id_trading_interval', 'at_network_flows', ['network_id', 'trading_interval'], unique=False, postgresql_using='btree')
    op.drop_index('idx_balancing_summary_network_id_interval', table_name='balancing_summary')
    op.create_index(op.f('ix_balancing_summary_network_region'), 'balancing_summary', ['network_region'], unique=False)
    op.alter_column('bom_station', 'state',
               existing_type=sa.TEXT(),
               nullable=False)
    op.alter_column('bom_station', 'name',
               existing_type=sa.TEXT(),
               nullable=False)
    op.alter_column('bom_station', 'priority',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('bom_station', 'is_capital',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.create_index(op.f('ix_bom_station_code'), 'bom_station', ['code'], unique=False)
    op.alter_column('facilities', 'name',
               existing_type=sa.TEXT(),
               nullable=False)
    op.alter_column('facilities', 'network_id',
               existing_type=sa.TEXT(),
               nullable=False)
    op.alter_column('facilities', 'network_region',
               existing_type=sa.TEXT(),
               nullable=False)
    op.alter_column('facilities', 'approved',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.drop_index('facility_scada_new_interval_idx', table_name='facility_scada')
    op.drop_index('idx_facility_scada_facility_code_interval', table_name='facility_scada')
    op.drop_index('idx_facility_scada_interval_facility_code', table_name='facility_scada')
    op.drop_index('idx_facility_scada_network_id', table_name='facility_scada')
    op.create_index(op.f('ix_facility_scada_network_id'), 'facility_scada', ['network_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_units_interconnector_region_to'), table_name='units')
    op.drop_index(op.f('ix_units_interconnector_region_from'), table_name='units')
    op.create_index('ix_facility_interconnector', 'units', ['interconnector'], unique=False)
    op.create_index('ix_facility_data_last_seen', 'units', ['data_last_seen'], unique=False)
    op.create_index('ix_facility_data_first_seen', 'units', ['data_first_seen'], unique=False)
    op.drop_index(op.f('ix_facility_scada_network_id'), table_name='facility_scada')
    op.create_index('idx_facility_scada_network_id', 'facility_scada', ['network_id'], unique=False)
    op.create_index('idx_facility_scada_interval_facility_code', 'facility_scada', ['interval', 'facility_code'], unique=False)
    op.create_index('idx_facility_scada_facility_code_interval', 'facility_scada', ['facility_code', sa.text('interval DESC')], unique=False)
    op.create_index('facility_scada_new_interval_idx', 'facility_scada', [sa.text('interval DESC')], unique=False)
    op.alter_column('facilities', 'approved',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column('facilities', 'network_region',
               existing_type=sa.TEXT(),
               nullable=True)
    op.alter_column('facilities', 'network_id',
               existing_type=sa.TEXT(),
               nullable=True)
    op.alter_column('facilities', 'name',
               existing_type=sa.TEXT(),
               nullable=True)
    op.drop_index(op.f('ix_bom_station_code'), table_name='bom_station')
    op.alter_column('bom_station', 'is_capital',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column('bom_station', 'priority',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('bom_station', 'name',
               existing_type=sa.TEXT(),
               nullable=True)
    op.alter_column('bom_station', 'state',
               existing_type=sa.TEXT(),
               nullable=True)
    op.drop_index(op.f('ix_balancing_summary_network_region'), table_name='balancing_summary')
    op.create_index('idx_balancing_summary_network_id_interval', 'balancing_summary', ['network_id', sa.text('interval DESC')], unique=False)
    op.create_index('balancing_summary_new_interval_idx', 'balancing_summary', [sa.text('interval DESC')], unique=False)
    op.drop_index('idx_at_network_flowsy_network_id_trading_interval', table_name='at_network_flows', postgresql_using='btree')
    op.create_index('idx_at_network_flowsy_network_id_trading_interval', 'at_network_flows', ['network_id', sa.text('trading_interval DESC')], unique=False)
    op.drop_index('idx_at_network_demand_network_id_trading_interval', table_name='at_network_demand', postgresql_using='btree')
    op.create_index('idx_at_network_demand_network_id_trading_interval', 'at_network_demand', ['network_id', sa.text('trading_day DESC')], unique=False)
    op.create_table('photo',
    sa.Column('station_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('mime_type', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('original_url', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('data', postgresql.BYTEA(), autoincrement=False, nullable=True),
    sa.Column('width', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('height', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('license_type', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('license_link', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('author', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('author_link', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('processed', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('processed_by', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('processed_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('approved', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('approved_by', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('approved_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('hash_id', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('is_primary', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('order', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['station_id'], ['facilities.id'], name='fk_photos_station_id')
    )
    op.create_index('ix_photo_hash_id', 'photo', ['hash_id'], unique=False)
    op.create_index('idx_photo_station_id', 'photo', ['station_id'], unique=False)
