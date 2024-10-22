# pylint: disable=no-member
"""
clean up station table

Revision ID: 57521fadef9e
Revises: e85a4bb70b9f
Create Date: 2024-10-24 10:50:43.579891

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '57521fadef9e'
down_revision = 'e85a4bb70b9f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('bom_station', 'priority',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('facility', 'active',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.alter_column('facility', 'approved',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.drop_column('facility', 'approved_by')
    op.drop_column('facility', 'include_in_geojson')
    op.drop_column('facility', 'approved_at')
    op.drop_index('facility_scada_new_interval_idx', table_name='facility_scada')
    op.create_index('facility_scada_new_interval_idx', 'facility_scada', ['interval'], unique=False, postgresql_ops={'interval': 'DESC'})
    op.drop_index('idx_facility_scada_interval_network', table_name='facility_scada')
    op.create_index('idx_facility_scada_interval_network', 'facility_scada', ['interval', 'network_id'], unique=False, postgresql_ops={'interval': 'DESC'})
    op.add_column('station', sa.Column('network_id', sa.Text(), nullable=True))
    op.add_column('station', sa.Column('network_region', sa.Text(), nullable=True))
    op.alter_column('station', 'name',
               existing_type=sa.TEXT(),
               nullable=False)
    op.alter_column('station', 'approved',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.drop_index('ix_station_network_code', table_name='station')
    op.create_foreign_key('fk_station_network_code', 'station', 'network', ['network_id'], ['code'])
    op.drop_column('station', 'approved_by')
    op.drop_column('station', 'network_code')
    op.drop_column('station', 'updated_at')
    op.drop_column('station', 'created_by')
    op.drop_column('station', 'created_at')
    op.drop_column('station', 'network_name')
    op.drop_column('station', 'approved_at')


def downgrade() -> None:
    op.add_column('station', sa.Column('approved_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('station', sa.Column('network_name', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('station', sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True))
    op.add_column('station', sa.Column('created_by', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('station', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('station', sa.Column('network_code', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('station', sa.Column('approved_by', sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_constraint('fk_station_network_code', 'station', type_='foreignkey')
    op.create_index('ix_station_network_code', 'station', ['network_code'], unique=False)
    op.alter_column('station', 'approved',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column('station', 'name',
               existing_type=sa.TEXT(),
               nullable=True)
    op.drop_column('station', 'network_region')
    op.drop_column('station', 'network_id')
    op.drop_index('idx_facility_scada_interval_network', table_name='facility_scada', postgresql_ops={'interval': 'DESC'})
    op.create_index('idx_facility_scada_interval_network', 'facility_scada', [sa.text('interval DESC'), 'network_id'], unique=False)
    op.drop_index('facility_scada_new_interval_idx', table_name='facility_scada', postgresql_ops={'interval': 'DESC'})
    op.create_index('facility_scada_new_interval_idx', 'facility_scada', [sa.text('interval DESC')], unique=False)
    op.add_column('facility', sa.Column('approved_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('facility', sa.Column('include_in_geojson', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('facility', sa.Column('approved_by', sa.TEXT(), autoincrement=False, nullable=True))
    op.alter_column('facility', 'approved',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column('facility', 'active',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column('bom_station', 'priority',
               existing_type=sa.INTEGER(),
               nullable=True)
