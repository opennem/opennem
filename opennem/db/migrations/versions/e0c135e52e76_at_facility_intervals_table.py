# pylint: disable=no-member
"""
at_facility_intervals table

Revision ID: e0c135e52e76
Revises: 2f6d8cb5bcdf
Create Date: 2024-11-13 09:04:15.149688

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'e0c135e52e76'
down_revision = '2f6d8cb5bcdf'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('at_facility_intervals',
    sa.Column('interval', sa.DateTime(), nullable=False),
    sa.Column('network_id', sa.Text(), nullable=False),
    sa.Column('facility_code', sa.Text(), nullable=False),
    sa.Column('unit_code', sa.Text(), nullable=False),
    sa.Column('fueltech_code', sa.Text(), nullable=False),
    sa.Column('network_region', sa.Text(), nullable=False),
    sa.Column('status_id', sa.Text(), nullable=True),
    sa.Column('generated', sa.Float(), nullable=True),
    sa.Column('energy', sa.Float(), nullable=True),
    sa.Column('emissions', sa.Float(), nullable=True),
    sa.Column('emissions_intensity', sa.Float(), nullable=True),
    sa.Column('market_value', sa.Float(), nullable=True),
    sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['network_id'], ['network.code'], name='fk_facility_aggregates_network_code'),
    sa.PrimaryKeyConstraint('interval', 'network_id', 'facility_code', 'unit_code')
    )
    op.create_index('idx_at_facility_intervals_facility_interval', 'at_facility_intervals', ['facility_code', sa.text('interval DESC')], unique=False)
    op.create_index('idx_at_facility_intervals_interval_network', 'at_facility_intervals', [sa.text('interval DESC'), 'network_id'], unique=False)
    op.create_index('idx_at_facility_intervals_network_region', 'at_facility_intervals', ['network_region'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_at_facility_intervals_network_region', table_name='at_facility_intervals')
    op.drop_index('idx_at_facility_intervals_interval_network', table_name='at_facility_intervals')
    op.drop_index('idx_at_facility_intervals_facility_interval', table_name='at_facility_intervals')
    op.drop_table('at_facility_intervals')
