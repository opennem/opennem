# pylint: disable=no-member
"""
remove unused tables

Revision ID: f9095c47b93c
Revises: 6f0b9e05ba9f
Create Date: 2024-09-14 14:17:59.548164

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f9095c47b93c'
down_revision = '6f0b9e05ba9f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('aemo_facility_data')
    op.drop_table('api_keys')
    op.drop_index('idx_at_network_flows_v3_trading_interval_facility_code', table_name='at_network_flows_v3')
    op.drop_index('idx_at_network_flowsy_v3_network_id_trading_interval', table_name='at_network_flows_v3')
    op.drop_index('ix_at_network_flows_v3_network_id', table_name='at_network_flows_v3')
    op.drop_index('ix_at_network_flows_v3_network_region', table_name='at_network_flows_v3')
    op.drop_index('ix_at_network_flows_v3_trading_interval', table_name='at_network_flows_v3')
    op.drop_table('at_network_flows_v3')
    op.drop_index('idx_at_facility_daily_network_id_trading_interval', table_name='at_facility_daily')


def downgrade() -> None:
    op.create_table('at_network_flows_v3',
    sa.Column('trading_interval', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=False),
    sa.Column('network_id', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('network_region', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('energy_imports', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('energy_exports', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('market_value_imports', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('market_value_exports', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('emissions_imports', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('emissions_exports', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['network_id'], ['network.code'], name='fk_at_network_flows_network_code'),
    sa.PrimaryKeyConstraint('trading_interval', 'network_id', 'network_region', name='at_network_flows_v3_pkey')
    )
    op.create_index('ix_at_network_flows_v3_trading_interval', 'at_network_flows_v3', ['trading_interval'], unique=False)
    op.create_index('ix_at_network_flows_v3_network_region', 'at_network_flows_v3', ['network_region'], unique=False)
    op.create_index('ix_at_network_flows_v3_network_id', 'at_network_flows_v3', ['network_id'], unique=False)
    op.create_index('idx_at_network_flowsy_v3_network_id_trading_interval', 'at_network_flows_v3', ['network_id', sa.text('trading_interval DESC')], unique=False)
    op.create_index('idx_at_network_flows_v3_trading_interval_facility_code', 'at_network_flows_v3', ['trading_interval', 'network_id', 'network_region'], unique=False)
    op.create_table('api_keys',
    sa.Column('keyid', sa.TEXT(), autoincrement=False, nullable=False),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('revoked', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('keyid', name='api_keys_pkey')
    )
    op.create_table('aemo_facility_data',
    sa.Column('aemo_source', postgresql.ENUM('rel', 'gi', name='aemodatasource'), autoincrement=False, nullable=False),
    sa.Column('source_date', sa.DATE(), autoincrement=False, nullable=False),
    sa.Column('name', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('name_network', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('network_region', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('fueltech_id', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('status_id', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('duid', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('units_no', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('capacity_registered', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('closure_year_expected', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('aemo_source', 'source_date', name='aemo_facility_data_pkey')
    )
