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
    op.create_table('aemo_market_notices',
    sa.Column('notice_id', sa.Integer(), nullable=False),
    sa.Column('notice_type', sa.String(), nullable=False),
    sa.Column('creation_date', sa.DateTime(), nullable=False),
    sa.Column('issue_date', sa.DateTime(), nullable=False),
    sa.Column('external_reference', sa.Text(), nullable=True),
    sa.Column('reason', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('notice_id')
    )
    op.create_index(op.f('ix_aemo_market_notices_creation_date'), 'aemo_market_notices', ['creation_date'], unique=False)
    op.create_index(op.f('ix_aemo_market_notices_notice_id'), 'aemo_market_notices', ['notice_id'], unique=False)
    op.create_index(op.f('ix_aemo_market_notices_notice_type'), 'aemo_market_notices', ['notice_type'], unique=False)
    op.create_table('milestones',
    sa.Column('record_id', sa.Text(), nullable=False),
    sa.Column('interval', sa.DateTime(), nullable=False),
    sa.Column('instance_id', sa.UUID(), nullable=False),
    sa.Column('aggregate', sa.String(), nullable=False),
    sa.Column('metric', sa.String(), nullable=True),
    sa.Column('period', sa.String(), nullable=True),
    sa.Column('significance', sa.Integer(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('value_unit', sa.String(), nullable=True),
    sa.Column('network_id', sa.Text(), nullable=True),
    sa.Column('network_region', sa.Text(), nullable=True),
    sa.Column('fueltech_id', sa.Text(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('description_long', sa.String(), nullable=True),
    sa.Column('previous_instance_id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['network_id'], ['network.code'], ),
    sa.PrimaryKeyConstraint('record_id', 'interval'),
    sa.UniqueConstraint('record_id', 'interval', name='excl_milestone_record_id_interval')
    )
    op.create_index('idx_milestone_fueltech_id', 'milestones', ['fueltech_id'], unique=False, postgresql_using='btree')
    op.create_index('idx_milestone_network_id', 'milestones', ['network_id'], unique=False, postgresql_using='btree')
    op.create_index(op.f('ix_milestones_interval'), 'milestones', ['interval'], unique=False)
    op.create_index(op.f('ix_milestones_record_id'), 'milestones', ['record_id'], unique=False)
    op.drop_index('idx_photo_station_id', table_name='photo')
    op.drop_index('ix_photo_hash_id', table_name='photo')
    op.drop_table('photo')
    op.drop_index('idx_at_network_demand_network_id_trading_interval', table_name='at_network_demand')
    op.create_index('idx_at_network_demand_network_id_trading_interval', 'at_network_demand', ['network_id', 'trading_day'], unique=False, postgresql_using='btree')
    op.drop_index('idx_at_network_flowsy_network_id_trading_interval', table_name='at_network_flows')
    op.create_index('idx_at_network_flowsy_network_id_trading_interval', 'at_network_flows', ['network_id', 'trading_interval'], unique=False, postgresql_using='btree')
    op.drop_index('balancing_summary_new_interval_idx', table_name='balancing_summary')
    op.drop_index('idx_balancing_summary_network_id_interval', table_name='balancing_summary')
    op.drop_index('idx_balancing_summary_network_id_network_region_interval', table_name='balancing_summary')
    op.create_index('idx_balancing_summary_interval_network_region', 'balancing_summary', ['interval', 'network_id', 'network_region'], unique=False, postgresql_ops={'interval': 'DESC'})
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
    op.drop_index('ix_station_code', table_name='facilities')
    op.drop_index('ix_station_network_code', table_name='facilities')
    op.create_index(op.f('ix_facilities_code'), 'facilities', ['code'], unique=True)
    op.add_column('facility_scada', sa.Column('eoi_quantity', sa.Numeric(), nullable=True))
    op.drop_index('facility_scada_new_interval_idx', table_name='facility_scada')
    op.drop_index('idx_facility_scada_facility_code_interval', table_name='facility_scada')
    op.drop_index('idx_facility_scada_interval_facility_code', table_name='facility_scada')
    op.drop_index('idx_facility_scada_network_id', table_name='facility_scada')
    op.create_index(op.f('ix_facility_scada_facility_code'), 'facility_scada', ['facility_code'], unique=False)
    op.create_index(op.f('ix_facility_scada_interval'), 'facility_scada', ['interval'], unique=False)
    op.create_index(op.f('ix_facility_scada_network_id'), 'facility_scada', ['network_id'], unique=False)
    op.drop_column('facility_status', 'updated_at')
    op.drop_column('facility_status', 'created_at')
    op.drop_column('facility_status', 'created_by')
    op.create_index('idx_fueltech_code', 'fueltech', ['code'], unique=False)
    op.add_column('fueltech_group', sa.Column('renewable', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.create_index('idx_network_code', 'network', ['code'], unique=False)
    op.drop_index('ix_stats_country_type', table_name='stats')
    op.drop_index('ix_stats_date', table_name='stats')
    op.drop_index('ix_facility_code', table_name='units')
    op.drop_index('ix_facility_data_first_seen', table_name='units')
    op.drop_index('ix_facility_data_last_seen', table_name='units')
    op.drop_index('ix_facility_interconnector', table_name='units')
    op.drop_index('ix_facility_interconnector_region_from', table_name='units')
    op.drop_index('ix_facility_interconnector_region_to', table_name='units')
    op.create_index('idx_facility_fueltech_id', 'units', ['fueltech_id'], unique=False)
    op.create_index(op.f('ix_units_code'), 'units', ['code'], unique=True)
    op.create_index(op.f('ix_units_data_first_seen'), 'units', ['data_first_seen'], unique=False)
    op.create_index(op.f('ix_units_data_last_seen'), 'units', ['data_last_seen'], unique=False)
    op.create_index(op.f('ix_units_interconnector'), 'units', ['interconnector'], unique=False)
    op.create_index(op.f('ix_units_interconnector_region_from'), 'units', ['interconnector_region_from'], unique=False)
    op.create_index(op.f('ix_units_interconnector_region_to'), 'units', ['interconnector_region_to'], unique=False)
    op.drop_constraint('fk_facility_station_code', 'units', type_='foreignkey')
    op.create_foreign_key('fk_unit_facility_id', 'units', 'facilities', ['station_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_unit_facility_id', 'units', type_='foreignkey')
    op.create_foreign_key('fk_facility_station_code', 'units', 'facilities', ['station_id'], ['id'], ondelete='CASCADE')
    op.drop_index(op.f('ix_units_interconnector_region_to'), table_name='units')
    op.drop_index(op.f('ix_units_interconnector_region_from'), table_name='units')
    op.drop_index(op.f('ix_units_interconnector'), table_name='units')
    op.drop_index(op.f('ix_units_data_last_seen'), table_name='units')
    op.drop_index(op.f('ix_units_data_first_seen'), table_name='units')
    op.drop_index(op.f('ix_units_code'), table_name='units')
    op.drop_index('idx_facility_fueltech_id', table_name='units')
    op.create_index('ix_facility_interconnector_region_to', 'units', ['interconnector_region_to'], unique=False)
    op.create_index('ix_facility_interconnector_region_from', 'units', ['interconnector_region_from'], unique=False)
    op.create_index('ix_facility_interconnector', 'units', ['interconnector'], unique=False)
    op.create_index('ix_facility_data_last_seen', 'units', ['data_last_seen'], unique=False)
    op.create_index('ix_facility_data_first_seen', 'units', ['data_first_seen'], unique=False)
    op.create_index('ix_facility_code', 'units', ['code'], unique=True)
    op.create_index('ix_stats_date', 'stats', [sa.text('stat_date DESC')], unique=False)
    op.create_index('ix_stats_country_type', 'stats', ['stat_type', 'country'], unique=False)
    op.drop_index('idx_network_code', table_name='network')
    op.drop_column('fueltech_group', 'renewable')
    op.drop_index('idx_fueltech_code', table_name='fueltech')
    op.add_column('facility_status', sa.Column('created_by', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('facility_status', sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True))
    op.add_column('facility_status', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.drop_index(op.f('ix_facility_scada_network_id'), table_name='facility_scada')
    op.drop_index(op.f('ix_facility_scada_interval'), table_name='facility_scada')
    op.drop_index(op.f('ix_facility_scada_facility_code'), table_name='facility_scada')
    op.create_index('idx_facility_scada_network_id', 'facility_scada', ['network_id'], unique=False)
    op.create_index('idx_facility_scada_interval_facility_code', 'facility_scada', ['interval', 'facility_code'], unique=False)
    op.create_index('idx_facility_scada_facility_code_interval', 'facility_scada', ['facility_code', sa.text('interval DESC')], unique=False)
    op.create_index('facility_scada_new_interval_idx', 'facility_scada', [sa.text('interval DESC')], unique=False)
    op.drop_column('facility_scada', 'eoi_quantity')
    op.drop_index(op.f('ix_facilities_code'), table_name='facilities')
    op.create_index('ix_station_network_code', 'facilities', ['network_id'], unique=False)
    op.create_index('ix_station_code', 'facilities', ['code'], unique=False)
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
    op.drop_index('idx_balancing_summary_interval_network_region', table_name='balancing_summary', postgresql_ops={'interval': 'DESC'})
    op.create_index('idx_balancing_summary_network_id_network_region_interval', 'balancing_summary', ['network_id', 'network_region', sa.text('interval DESC')], unique=False)
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
    op.drop_index(op.f('ix_milestones_record_id'), table_name='milestones')
    op.drop_index(op.f('ix_milestones_interval'), table_name='milestones')
    op.drop_index('idx_milestone_network_id', table_name='milestones', postgresql_using='btree')
    op.drop_index('idx_milestone_fueltech_id', table_name='milestones', postgresql_using='btree')
    op.drop_table('milestones')
    op.drop_index(op.f('ix_aemo_market_notices_notice_type'), table_name='aemo_market_notices')
    op.drop_index(op.f('ix_aemo_market_notices_notice_id'), table_name='aemo_market_notices')
    op.drop_index(op.f('ix_aemo_market_notices_creation_date'), table_name='aemo_market_notices')
    op.drop_table('aemo_market_notices')
