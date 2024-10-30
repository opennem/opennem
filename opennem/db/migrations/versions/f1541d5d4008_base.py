# pylint: disable=no-member
"""
base

Revision ID: f1541d5d4008
Revises:
Create Date: 2024-11-08 00:44:28.031361

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f1541d5d4008'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
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
    op.create_table('balancing_summary',
    sa.Column('network_id', sa.Text(), nullable=False),
    sa.Column('interval', postgresql.TIMESTAMP(), nullable=False),
    sa.Column('network_region', sa.Text(), nullable=False),
    sa.Column('forecast_load', sa.Numeric(), nullable=True),
    sa.Column('generation_scheduled', sa.Numeric(), nullable=True),
    sa.Column('generation_non_scheduled', sa.Numeric(), nullable=True),
    sa.Column('generation_total', sa.Numeric(), nullable=True),
    sa.Column('net_interchange', sa.Numeric(), nullable=True),
    sa.Column('demand', sa.Numeric(), nullable=True),
    sa.Column('demand_total', sa.Numeric(), nullable=True),
    sa.Column('price', sa.Numeric(), nullable=True),
    sa.Column('price_dispatch', sa.Numeric(), nullable=True),
    sa.Column('net_interchange_trading', sa.Numeric(), nullable=True),
    sa.Column('is_forecast', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('network_id', 'interval', 'network_region')
    )
    op.create_index('idx_balancing_summary_interval_network_region', 'balancing_summary', ['interval', 'network_id', 'network_region'], unique=False, postgresql_ops={'interval': 'DESC'})
    op.create_index('idx_balancing_summary_network_id_interval', 'balancing_summary', ['network_id', 'interval'], unique=False, postgresql_using='btree')
    op.create_index(op.f('ix_balancing_summary_interval'), 'balancing_summary', ['interval'], unique=False)
    op.create_table('bom_station',
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('state', sa.Text(), nullable=True),
    sa.Column('name', sa.Text(), nullable=True),
    sa.Column('web_code', sa.Text(), nullable=True),
    sa.Column('name_alias', sa.Text(), nullable=True),
    sa.Column('registered', sa.Date(), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('is_capital', sa.Boolean(), nullable=True),
    sa.Column('website_url', sa.Text(), nullable=True),
    sa.Column('feed_url', sa.Text(), nullable=True),
    sa.Column('altitude', sa.Integer(), nullable=True),
    sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry'), nullable=True),
    sa.PrimaryKeyConstraint('code')
    )
    op.create_index('idx_bom_station_geom', 'bom_station', ['geom'], unique=False, postgresql_using='gist')
    op.create_index('idx_bom_station_priority', 'bom_station', ['priority'], unique=False, postgresql_using='btree')
    op.create_table('crawl_meta',
    sa.Column('spider_name', sa.Text(), nullable=False),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('spider_name')
    )
    op.create_index(op.f('ix_crawl_meta_data'), 'crawl_meta', ['data'], unique=False)
    op.create_table('facilities',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('network_id', sa.Text(), nullable=False),
    sa.Column('network_region', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('website_url', sa.Text(), nullable=True),
    sa.Column('wikipedia_link', sa.Text(), nullable=True),
    sa.Column('wikidata_id', sa.Text(), nullable=True),
    sa.Column('approved', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code', name='excl_station_network_duid')
    )
    op.create_index(op.f('ix_facilities_code'), 'facilities', ['code'], unique=True)
    op.create_table('facility_scada',
    sa.Column('interval', postgresql.TIMESTAMP(), nullable=False),
    sa.Column('network_id', sa.Text(), nullable=False),
    sa.Column('facility_code', sa.Text(), nullable=False),
    sa.Column('generated', sa.Numeric(), nullable=True),
    sa.Column('is_forecast', sa.Boolean(), nullable=False),
    sa.Column('eoi_quantity', sa.Numeric(), nullable=True),
    sa.Column('energy', sa.Numeric(), nullable=True),
    sa.Column('energy_quality_flag', sa.Numeric(), nullable=False),
    sa.PrimaryKeyConstraint('interval', 'network_id', 'facility_code', 'is_forecast')
    )
    op.create_index('facility_scada_new_interval_idx', 'facility_scada', ['interval'], unique=False, postgresql_ops={'interval': 'DESC'})
    op.create_index('idx_facility_scada_facility_code_interval', 'facility_scada', ['facility_code', 'interval'], unique=False, postgresql_using='btree')
    op.create_index('idx_facility_scada_interval_facility_code', 'facility_scada', ['interval', 'facility_code'], unique=False)
    op.create_index('idx_facility_scada_interval_network', 'facility_scada', ['interval', 'network_id'], unique=False, postgresql_ops={'interval': 'DESC'})
    op.create_index('idx_facility_scada_is_forecast_interval', 'facility_scada', ['is_forecast', 'interval'], unique=False)
    op.create_index('idx_facility_scada_network_facility_interval', 'facility_scada', ['network_id', 'facility_code', 'interval'], unique=False)
    op.create_index('idx_facility_scada_network_id', 'facility_scada', ['network_id'], unique=False)
    op.create_index('idx_facility_scada_network_interval', 'facility_scada', ['network_id', 'interval', 'is_forecast'], unique=False)
    op.create_index(op.f('ix_facility_scada_facility_code'), 'facility_scada', ['facility_code'], unique=False)
    op.create_index(op.f('ix_facility_scada_interval'), 'facility_scada', ['interval'], unique=False)
    op.create_table('facility_status',
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('label', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('code')
    )
    op.create_table('feedback',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('subject', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('email', sa.Text(), nullable=True),
    sa.Column('twitter', sa.Text(), nullable=True),
    sa.Column('user_ip', sa.Text(), nullable=True),
    sa.Column('user_agent', sa.Text(), nullable=True),
    sa.Column('alert_sent', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('fueltech_group',
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('label', sa.Text(), nullable=True),
    sa.Column('color', sa.Text(), nullable=True),
    sa.Column('renewable', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('created_by', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('code')
    )
    op.create_table('network',
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('country', sa.Text(), nullable=False),
    sa.Column('label', sa.Text(), nullable=True),
    sa.Column('timezone', sa.Text(), nullable=False),
    sa.Column('timezone_database', sa.Text(), nullable=True),
    sa.Column('offset', sa.Integer(), nullable=True),
    sa.Column('interval_size', sa.Integer(), nullable=False),
    sa.Column('data_start_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('data_end_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('network_price', sa.Text(), nullable=False),
    sa.Column('interval_shift', sa.Integer(), nullable=False),
    sa.Column('export_set', sa.Boolean(), nullable=False),
    sa.Column('created_by', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('code')
    )
    op.create_index('idx_network_code', 'network', ['code'], unique=False)
    op.create_index(op.f('ix_network_data_end_date'), 'network', ['data_end_date'], unique=False)
    op.create_index(op.f('ix_network_data_start_date'), 'network', ['data_start_date'], unique=False)
    op.create_table('stats',
    sa.Column('stat_date', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('country', sa.Text(), nullable=False),
    sa.Column('stat_type', sa.Text(), nullable=False),
    sa.Column('value', sa.Numeric(), nullable=True),
    sa.Column('created_by', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('stat_date', 'country', 'stat_type')
    )
    op.create_index(op.f('ix_stats_stat_date'), 'stats', ['stat_date'], unique=False)
    op.create_table('at_network_demand',
    sa.Column('trading_day', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('network_id', sa.Text(), nullable=False),
    sa.Column('network_region', sa.Text(), nullable=False),
    sa.Column('demand_energy', sa.Numeric(), nullable=True),
    sa.Column('demand_market_value', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['network_id'], ['network.code'], name='fk_at_facility_daily_network_code'),
    sa.PrimaryKeyConstraint('trading_day', 'network_id', 'network_region')
    )
    op.create_index('idx_at_network_demand_network_id_trading_interval', 'at_network_demand', ['network_id', 'trading_day'], unique=False, postgresql_using='btree')
    op.create_index('idx_at_network_demand_trading_interval_network_region', 'at_network_demand', ['trading_day', 'network_id', 'network_region'], unique=False)
    op.create_index(op.f('ix_at_network_demand_network_id'), 'at_network_demand', ['network_id'], unique=False)
    op.create_index(op.f('ix_at_network_demand_trading_day'), 'at_network_demand', ['trading_day'], unique=False)
    op.create_table('at_network_flows',
    sa.Column('trading_interval', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('network_id', sa.Text(), nullable=False),
    sa.Column('network_region', sa.Text(), nullable=False),
    sa.Column('energy_imports', sa.Numeric(), nullable=True),
    sa.Column('energy_exports', sa.Numeric(), nullable=True),
    sa.Column('market_value_imports', sa.Numeric(), nullable=True),
    sa.Column('market_value_exports', sa.Numeric(), nullable=True),
    sa.Column('emissions_imports', sa.Numeric(), nullable=True),
    sa.Column('emissions_exports', sa.Numeric(), nullable=True),
    sa.ForeignKeyConstraint(['network_id'], ['network.code'], name='fk_at_network_flows_network_code'),
    sa.PrimaryKeyConstraint('trading_interval', 'network_id', 'network_region')
    )
    op.create_index('idx_at_network_flows_trading_interval_facility_code', 'at_network_flows', ['trading_interval', 'network_id', 'network_region'], unique=False)
    op.create_index('idx_at_network_flowsy_network_id_trading_interval', 'at_network_flows', ['network_id', 'trading_interval'], unique=False, postgresql_using='btree')
    op.create_index(op.f('ix_at_network_flows_network_id'), 'at_network_flows', ['network_id'], unique=False)
    op.create_index(op.f('ix_at_network_flows_network_region'), 'at_network_flows', ['network_region'], unique=False)
    op.create_index(op.f('ix_at_network_flows_trading_interval'), 'at_network_flows', ['trading_interval'], unique=False)
    op.create_table('bom_observation',
    sa.Column('observation_time', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('station_id', sa.Text(), nullable=False),
    sa.Column('temp_apparent', sa.Numeric(), nullable=True),
    sa.Column('temp_air', sa.Numeric(), nullable=True),
    sa.Column('temp_min', sa.Numeric(), nullable=True),
    sa.Column('temp_max', sa.Numeric(), nullable=True),
    sa.Column('press_qnh', sa.Numeric(), nullable=True),
    sa.Column('wind_dir', sa.Text(), nullable=True),
    sa.Column('wind_spd', sa.Numeric(), nullable=True),
    sa.Column('wind_gust', sa.Numeric(), nullable=True),
    sa.Column('humidity', sa.Numeric(), nullable=True),
    sa.Column('cloud', sa.Text(), nullable=True),
    sa.Column('cloud_type', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['station_id'], ['bom_station.code'], name='fk_bom_observation_station_code'),
    sa.PrimaryKeyConstraint('observation_time', 'station_id')
    )
    op.create_index(op.f('ix_bom_observation_observation_time'), 'bom_observation', ['observation_time'], unique=False)
    op.create_table('crawl_history',
    sa.Column('source', sa.Enum('nemweb', 'wem', name='crawlersource'), nullable=False),
    sa.Column('crawler_name', sa.Text(), nullable=False),
    sa.Column('network_id', sa.Text(), nullable=False),
    sa.Column('interval', postgresql.TIMESTAMP(timezone=True), nullable=False),
    sa.Column('inserted_records', sa.Integer(), nullable=True),
    sa.Column('crawled_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('processed_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['network_id'], ['network.code'], name='fk_crawl_info_network_code'),
    sa.PrimaryKeyConstraint('source', 'crawler_name', 'network_id', 'interval')
    )
    op.create_index(op.f('ix_crawl_history_interval'), 'crawl_history', ['interval'], unique=False)
    op.create_table('fueltech',
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('label', sa.Text(), nullable=True),
    sa.Column('renewable', sa.Boolean(), nullable=True),
    sa.Column('fueltech_group_id', sa.Text(), nullable=True),
    sa.Column('created_by', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['fueltech_group_id'], ['fueltech_group.code'], ),
    sa.PrimaryKeyConstraint('code')
    )
    op.create_index('idx_fueltech_code', 'fueltech', ['code'], unique=False)
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
    op.create_table('network_region',
    sa.Column('network_id', sa.Text(), nullable=False),
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('timezone', sa.Text(), nullable=True),
    sa.Column('timezone_database', sa.Text(), nullable=True),
    sa.Column('offset', sa.Integer(), nullable=True),
    sa.Column('export_set', sa.Boolean(), nullable=False),
    sa.Column('created_by', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['network_id'], ['network.code'], name='fk_network_region_network_code'),
    sa.PrimaryKeyConstraint('network_id', 'code')
    )
    op.create_table('units',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('fueltech_id', sa.Text(), nullable=True),
    sa.Column('status_id', sa.Text(), nullable=True),
    sa.Column('station_id', sa.Integer(), nullable=True),
    sa.Column('dispatch_type', sa.Text(), nullable=False),
    sa.Column('capacity_registered', sa.Numeric(), nullable=True),
    sa.Column('registered', sa.DateTime(), nullable=True),
    sa.Column('deregistered', sa.DateTime(), nullable=True),
    sa.Column('expected_closure_date', sa.DateTime(), nullable=True),
    sa.Column('expected_closure_year', sa.Integer(), nullable=True),
    sa.Column('unit_id', sa.Integer(), nullable=True),
    sa.Column('unit_number', sa.Integer(), nullable=True),
    sa.Column('unit_alias', sa.Text(), nullable=True),
    sa.Column('unit_capacity', sa.Numeric(), nullable=True),
    sa.Column('emissions_factor_co2', sa.Numeric(), nullable=True),
    sa.Column('emission_factor_source', sa.Text(), nullable=True),
    sa.Column('interconnector', sa.Boolean(), nullable=False),
    sa.Column('interconnector_region_to', sa.Text(), nullable=True),
    sa.Column('interconnector_region_from', sa.Text(), nullable=True),
    sa.Column('data_first_seen', sa.DateTime(timezone=True), nullable=True),
    sa.Column('data_last_seen', sa.DateTime(timezone=True), nullable=True),
    sa.Column('approved', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['fueltech_id'], ['fueltech.code'], name='fk_unit_fueltech_code'),
    sa.ForeignKeyConstraint(['station_id'], ['facilities.id'], name='fk_unit_facility_id'),
    sa.ForeignKeyConstraint(['status_id'], ['facility_status.code'], name='fk_unit_facility_status_code'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_facility_fueltech_id', 'units', ['fueltech_id'], unique=False)
    op.create_index('idx_facility_station_id', 'units', ['station_id'], unique=False, postgresql_using='btree')
    op.create_index(op.f('ix_units_code'), 'units', ['code'], unique=True)
    op.create_index(op.f('ix_units_data_first_seen'), 'units', ['data_first_seen'], unique=False)
    op.create_index(op.f('ix_units_data_last_seen'), 'units', ['data_last_seen'], unique=False)
    op.create_index(op.f('ix_units_interconnector'), 'units', ['interconnector'], unique=False)
    op.create_index(op.f('ix_units_interconnector_region_from'), 'units', ['interconnector_region_from'], unique=False)
    op.create_index(op.f('ix_units_interconnector_region_to'), 'units', ['interconnector_region_to'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_units_interconnector_region_to'), table_name='units')
    op.drop_index(op.f('ix_units_interconnector_region_from'), table_name='units')
    op.drop_index(op.f('ix_units_interconnector'), table_name='units')
    op.drop_index(op.f('ix_units_data_last_seen'), table_name='units')
    op.drop_index(op.f('ix_units_data_first_seen'), table_name='units')
    op.drop_index(op.f('ix_units_code'), table_name='units')
    op.drop_index('idx_facility_station_id', table_name='units', postgresql_using='btree')
    op.drop_index('idx_facility_fueltech_id', table_name='units')
    op.drop_table('units')
    op.drop_table('network_region')
    op.drop_index(op.f('ix_milestones_record_id'), table_name='milestones')
    op.drop_index(op.f('ix_milestones_interval'), table_name='milestones')
    op.drop_index('idx_milestone_network_id', table_name='milestones', postgresql_using='btree')
    op.drop_index('idx_milestone_fueltech_id', table_name='milestones', postgresql_using='btree')
    op.drop_table('milestones')
    op.drop_index('idx_fueltech_code', table_name='fueltech')
    op.drop_table('fueltech')
    op.drop_index(op.f('ix_crawl_history_interval'), table_name='crawl_history')
    op.drop_table('crawl_history')
    op.drop_index(op.f('ix_bom_observation_observation_time'), table_name='bom_observation')
    op.drop_table('bom_observation')
    op.drop_index(op.f('ix_at_network_flows_trading_interval'), table_name='at_network_flows')
    op.drop_index(op.f('ix_at_network_flows_network_region'), table_name='at_network_flows')
    op.drop_index(op.f('ix_at_network_flows_network_id'), table_name='at_network_flows')
    op.drop_index('idx_at_network_flowsy_network_id_trading_interval', table_name='at_network_flows', postgresql_using='btree')
    op.drop_index('idx_at_network_flows_trading_interval_facility_code', table_name='at_network_flows')
    op.drop_table('at_network_flows')
    op.drop_index(op.f('ix_at_network_demand_trading_day'), table_name='at_network_demand')
    op.drop_index(op.f('ix_at_network_demand_network_id'), table_name='at_network_demand')
    op.drop_index('idx_at_network_demand_trading_interval_network_region', table_name='at_network_demand')
    op.drop_index('idx_at_network_demand_network_id_trading_interval', table_name='at_network_demand', postgresql_using='btree')
    op.drop_table('at_network_demand')
    op.drop_index(op.f('ix_stats_stat_date'), table_name='stats')
    op.drop_table('stats')
    op.drop_index(op.f('ix_network_data_start_date'), table_name='network')
    op.drop_index(op.f('ix_network_data_end_date'), table_name='network')
    op.drop_index('idx_network_code', table_name='network')
    op.drop_table('network')
    op.drop_table('fueltech_group')
    op.drop_table('feedback')
    op.drop_table('facility_status')
    op.drop_index(op.f('ix_facility_scada_interval'), table_name='facility_scada')
    op.drop_index(op.f('ix_facility_scada_facility_code'), table_name='facility_scada')
    op.drop_index('idx_facility_scada_network_interval', table_name='facility_scada')
    op.drop_index('idx_facility_scada_network_id', table_name='facility_scada')
    op.drop_index('idx_facility_scada_network_facility_interval', table_name='facility_scada')
    op.drop_index('idx_facility_scada_is_forecast_interval', table_name='facility_scada')
    op.drop_index('idx_facility_scada_interval_network', table_name='facility_scada', postgresql_ops={'interval': 'DESC'})
    op.drop_index('idx_facility_scada_interval_facility_code', table_name='facility_scada')
    op.drop_index('idx_facility_scada_facility_code_interval', table_name='facility_scada', postgresql_using='btree')
    op.drop_index('facility_scada_new_interval_idx', table_name='facility_scada', postgresql_ops={'interval': 'DESC'})
    op.drop_table('facility_scada')
    op.drop_index(op.f('ix_facilities_code'), table_name='facilities')
    op.drop_table('facilities')
    op.drop_index(op.f('ix_crawl_meta_data'), table_name='crawl_meta')
    op.drop_table('crawl_meta')
    op.drop_index('idx_bom_station_priority', table_name='bom_station', postgresql_using='btree')
    op.drop_index('idx_bom_station_geom', table_name='bom_station', postgresql_using='gist')
    op.drop_table('bom_station')
    op.drop_index(op.f('ix_balancing_summary_interval'), table_name='balancing_summary')
    op.drop_index('idx_balancing_summary_network_id_interval', table_name='balancing_summary', postgresql_using='btree')
    op.drop_index('idx_balancing_summary_interval_network_region', table_name='balancing_summary', postgresql_ops={'interval': 'DESC'})
    op.drop_table('balancing_summary')
    op.drop_index(op.f('ix_aemo_market_notices_notice_type'), table_name='aemo_market_notices')
    op.drop_index(op.f('ix_aemo_market_notices_notice_id'), table_name='aemo_market_notices')
    op.drop_index(op.f('ix_aemo_market_notices_creation_date'), table_name='aemo_market_notices')
    op.drop_table('aemo_market_notices')
    # ### end Alembic commands ###
