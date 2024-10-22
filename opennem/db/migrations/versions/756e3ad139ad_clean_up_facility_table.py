# pylint: disable=no-member
"""
clean up facility table

Revision ID: 756e3ad139ad
Revises: 57521fadef9e
Create Date: 2024-10-24 19:29:33.809330

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '756e3ad139ad'
down_revision = '57521fadef9e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("drop materialized view if exists mv_fueltech_daily")
    op.drop_constraint('excl_facility_network_id_code', 'facility', type_='unique')
    op.drop_index('ix_facility_network_code', table_name='facility')
    op.drop_index('ix_facility_network_region', table_name='facility')
    op.drop_constraint('fk_station_network_code', 'facility', type_='foreignkey')
    op.drop_column('facility', 'network_id')
    op.drop_column('facility', 'network_name')
    op.drop_column('facility', 'active')
    op.drop_column('facility', 'created_at')
    op.drop_column('facility', 'network_region', cascade=True)
    op.drop_column('facility', 'updated_at')
    op.drop_column('facility', 'network_code')
    op.drop_column('facility', 'created_by')


def downgrade() -> None:
    op.add_column('facility', sa.Column('created_by', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('facility', sa.Column('network_code', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('facility', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('facility', sa.Column('network_region', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('facility', sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True))
    op.add_column('facility', sa.Column('active', sa.BOOLEAN(), autoincrement=False, nullable=False))
    op.add_column('facility', sa.Column('network_name', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('facility', sa.Column('network_id', sa.TEXT(), autoincrement=False, nullable=False))
    op.create_foreign_key('fk_station_network_code', 'facility', 'network', ['network_id'], ['code'])
    op.create_index('ix_facility_network_region', 'facility', ['network_region'], unique=False)
    op.create_index('ix_facility_network_code', 'facility', ['network_code'], unique=False)
    op.create_unique_constraint('excl_facility_network_id_code', 'facility', ['network_id', 'code'])
