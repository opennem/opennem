# pylint: disable=no-member
"""
flows table v4

Revision ID: e167bf2a27e2
Revises: ea9674fa02bb
Create Date: 2024-11-15 19:16:22.667874

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e167bf2a27e2'
down_revision = 'ea9674fa02bb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('at_network_flows_interval_idx', table_name='at_network_flows')
    op.drop_index('idx_at_network_flows_network_id_interval', table_name='at_network_flows')
    op.create_index('idx_at_network_flows_network_id_trading_interval', 'at_network_flows', ['network_id', 'interval'], unique=False, postgresql_using='btree')
    op.create_index('idx_at_network_flows_trading_interval_facility_code', 'at_network_flows', ['interval', 'network_id', 'network_region'], unique=False)
    op.create_index(op.f('ix_at_network_flows_interval'), 'at_network_flows', ['interval'], unique=False)
    op.create_foreign_key('fk_at_network_flows_network_code', 'at_network_flows', 'network', ['network_id'], ['code'])


def downgrade() -> None:
    op.drop_constraint('fk_at_network_flows_network_code', 'at_network_flows', type_='foreignkey')
    op.drop_index(op.f('ix_at_network_flows_interval'), table_name='at_network_flows')
    op.drop_index('idx_at_network_flows_trading_interval_facility_code', table_name='at_network_flows')
    op.drop_index('idx_at_network_flows_network_id_trading_interval', table_name='at_network_flows', postgresql_using='btree')
    op.create_index('idx_at_network_flows_network_id_interval', 'at_network_flows', ['network_id', 'interval'], unique=False)
    op.create_index('at_network_flows_interval_idx', 'at_network_flows', [sa.text('interval DESC')], unique=False)
