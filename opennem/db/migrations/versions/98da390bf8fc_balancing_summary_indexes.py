# pylint: disable=no-member
"""
balancing_summary indexes

Revision ID: 98da390bf8fc
Revises: 50b567dd8ab1
Create Date: 2024-11-09 22:58:17.125247

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '98da390bf8fc'
down_revision = '50b567dd8ab1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('idx_balancing_summary_interval_network_region', table_name='balancing_summary')
    op.create_index('idx_balancing_summary_interval_network_region', 'balancing_summary', ['interval', 'network_id', 'network_region'], unique=False, postgresql_ops={'interval': 'DESC'})
    op.create_index('idx_balancing_price_lookup', 'balancing_summary', ['interval', 'network_id', 'network_region', 'price'], unique=False, postgresql_where=sa.text('is_forecast = false AND price IS NOT NULL'), postgresql_using='btree')
    op.create_index('idx_balancing_region_time', 'balancing_summary', ['network_region', 'interval', 'is_forecast'], unique=False, postgresql_using='btree')
    op.create_index('idx_balancing_time_lookup', 'balancing_summary', ['interval', 'network_id', 'network_region', 'is_forecast'], unique=False, postgresql_using='btree')


def downgrade() -> None:
    op.drop_index('idx_balancing_time_lookup', table_name='balancing_summary', postgresql_using='btree')
    op.drop_index('idx_balancing_region_time', table_name='balancing_summary', postgresql_using='btree')
    op.drop_index('idx_balancing_price_lookup', table_name='balancing_summary', postgresql_where=sa.text('is_forecast = false AND price IS NOT NULL'), postgresql_using='btree')
    op.drop_index('idx_balancing_summary_interval_network_region', table_name='balancing_summary', postgresql_ops={'interval': 'DESC'})
    op.create_index('idx_balancing_summary_interval_network_region', 'balancing_summary', [sa.text('interval DESC'), 'network_id', 'network_region'], unique=False)
