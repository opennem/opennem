# pylint: disable=no-member
"""
cleanup indexes

Revision ID: e85a4bb70b9f
Revises: 441113b529a5
Create Date: 2024-10-24 09:51:26.252142

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e85a4bb70b9f'
down_revision = '441113b529a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('idx_at_facility_daily_facility_code_network_id_trading_day', table_name='at_facility_daily')
    op.drop_index('idx_at_facility_daily_trading_interval_facility_code', table_name='at_facility_daily')
    op.drop_index('idx_at_facility_day_facility_code_trading_interval', table_name='at_facility_daily')


    op.drop_index('idx_at_network_demand_network_id_trading_interval', table_name='at_network_demand')
    op.create_index('idx_at_network_demand_network_id_trading_interval', 'at_network_demand', ['network_id', 'trading_day'], unique=False, postgresql_using='btree')

    op.drop_index('idx_at_network_flowsy_network_id_trading_interval', table_name='at_network_flows')
    op.create_index('idx_at_network_flowsy_network_id_trading_interval', 'at_network_flows', ['network_id', 'trading_interval'], unique=False, postgresql_using='btree')

    op.drop_index('balancing_summary_new_interval_idx', table_name='balancing_summary')
    op.drop_index('idx_balancing_summary_interval_network_region', table_name='balancing_summary')
    op.create_index('idx_balancing_summary_interval_network_region', 'balancing_summary', ['interval', 'network_id', 'network_region'], unique=False, postgresql_ops={'interval': 'DESC'})
    op.drop_index('idx_balancing_summary_network_id_interval', table_name='balancing_summary')
    op.create_index('idx_balancing_summary_network_id_interval', 'balancing_summary', ['network_id', 'interval'], unique=False, postgresql_using='btree')

    op.drop_index('facility_scada_new_interval_idx', table_name='facility_scada')
    op.create_index('facility_scada_new_interval_idx', 'facility_scada', ['interval'], unique=False, postgresql_ops={'interval': 'DESC'})
    op.drop_index('idx_facility_scada_facility_code_interval', table_name='facility_scada')
    op.create_index('idx_facility_scada_facility_code_interval', 'facility_scada', ['facility_code', 'interval'], unique=False, postgresql_using='btree')
    op.drop_index('idx_facility_scada_interval_network', table_name='facility_scada')
    op.create_index('idx_facility_scada_interval_network', 'facility_scada', ['interval', 'network_id'], unique=False, postgresql_ops={'interval': 'DESC'})


def downgrade() -> None:
    op.drop_index('idx_facility_scada_interval_network', table_name='facility_scada', postgresql_ops={'interval': 'DESC'})
    op.create_index('idx_facility_scada_interval_network', 'facility_scada', [sa.text('interval DESC'), 'network_id'], unique=False)
    op.drop_index('idx_facility_scada_facility_code_interval', table_name='facility_scada', postgresql_using='btree')
    op.create_index('idx_facility_scada_facility_code_interval', 'facility_scada', ['facility_code', sa.text('interval DESC')], unique=False)
    op.drop_index('facility_scada_new_interval_idx', table_name='facility_scada', postgresql_ops={'interval': 'DESC'})
    op.create_index('facility_scada_new_interval_idx', 'facility_scada', [sa.text('interval DESC')], unique=False)


    op.drop_index('idx_balancing_summary_network_id_interval', table_name='balancing_summary', postgresql_using='btree')
    op.create_index('idx_balancing_summary_network_id_interval', 'balancing_summary', ['network_id', sa.text('interval DESC')], unique=False)
    op.drop_index('idx_balancing_summary_interval_network_region', table_name='balancing_summary', postgresql_ops={'interval': 'DESC'})
    op.create_index('idx_balancing_summary_interval_network_region', 'balancing_summary', [sa.text('interval DESC'), 'network_id', 'network_region'], unique=False)
    op.create_index('balancing_summary_new_interval_idx', 'balancing_summary', [sa.text('interval DESC')], unique=False)
    op.drop_index('idx_at_network_flowsy_network_id_trading_interval', table_name='at_network_flows', postgresql_using='btree')
    op.create_index('idx_at_network_flowsy_network_id_trading_interval', 'at_network_flows', ['network_id', sa.text('trading_interval DESC')], unique=False)
    op.drop_index('idx_at_network_demand_network_id_trading_interval', table_name='at_network_demand', postgresql_using='btree')

    op.create_index('idx_at_network_demand_network_id_trading_interval', 'at_network_demand', ['network_id', sa.text('trading_day DESC')], unique=False)
    op.create_index('idx_at_facility_day_facility_code_trading_interval', 'at_facility_daily', ['facility_code', sa.text('trading_day DESC')], unique=False)
    op.create_index('idx_at_facility_daily_trading_interval_facility_code', 'at_facility_daily', ['trading_day', 'facility_code'], unique=False)
    op.create_index('idx_at_facility_daily_facility_code_network_id_trading_day', 'at_facility_daily', ['network_id', 'facility_code', 'trading_day'], unique=True)
    # ### end Alembic commands ###
