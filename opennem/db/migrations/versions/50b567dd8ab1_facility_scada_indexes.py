# pylint: disable=no-member
"""
facility scada indexes

Revision ID: 50b567dd8ab1
Revises: 7d6b0be0009e
Create Date: 2024-11-09 13:17:18.708446

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '50b567dd8ab1'
down_revision = '7d6b0be0009e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('idx_facility_scada_facility_code_interval', 'facility_scada', ['facility_code', sa.text('interval DESC')], unique=False)
    op.create_index('idx_facility_scada_group', 'facility_scada', ['network_id', 'facility_code', 'generated', 'energy'], unique=False, postgresql_using='btree')
    op.create_index('idx_facility_scada_interval_bucket', 'facility_scada', ['interval', 'network_id', 'facility_code', 'is_forecast'], unique=False, postgresql_using='btree')
    op.create_index('idx_facility_scada_interval_facility_code', 'facility_scada', ['interval', 'facility_code'], unique=False)
    op.create_index('idx_facility_scada_network_id', 'facility_scada', ['network_id'], unique=False)
    op.create_index('idx_facility_scada_non_forecast', 'facility_scada', ['interval', 'facility_code', 'generated', 'energy'], unique=False, postgresql_where=sa.text('is_forecast = false'), postgresql_using='btree')


def downgrade() -> None:
    op.drop_index('idx_facility_scada_non_forecast', table_name='facility_scada', postgresql_where=sa.text('is_forecast = false'), postgresql_using='btree')
    op.drop_index('idx_facility_scada_network_id', table_name='facility_scada')
    op.drop_index('idx_facility_scada_interval_facility_code', table_name='facility_scada')
    op.drop_index('idx_facility_scada_interval_bucket', table_name='facility_scada', postgresql_using='btree')
    op.drop_index('idx_facility_scada_group', table_name='facility_scada', postgresql_using='btree')
    op.drop_index('idx_facility_scada_facility_code_interval', table_name='facility_scada')
