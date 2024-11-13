# pylint: disable=no-member
"""
at_facility_intervals indexes

Revision ID: ea9674fa02bb
Revises: e0c135e52e76
Create Date: 2024-11-13 09:50:50.152178

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = 'ea9674fa02bb'
down_revision = 'e0c135e52e76'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('idx_at_facility_intervals_time_facility', 'at_facility_intervals', [sa.text('interval DESC'), 'facility_code'], unique=False)
    op.create_index('idx_at_facility_intervals_unit_time', 'at_facility_intervals', ['unit_code', sa.text('interval DESC')], unique=False)
    op.create_index(op.f('ix_at_facility_intervals_facility_code'), 'at_facility_intervals', ['facility_code'], unique=False)
    op.create_index(op.f('ix_at_facility_intervals_network_id'), 'at_facility_intervals', ['network_id'], unique=False)
    op.create_index(op.f('ix_at_facility_intervals_unit_code'), 'at_facility_intervals', ['unit_code'], unique=False)
    op.drop_index('idx_balancing_summary_interval_network_region', table_name='balancing_summary')
    op.create_index('idx_balancing_summary_interval_network_region', 'balancing_summary', ['interval', 'network_id', 'network_region'], unique=False, postgresql_ops={'interval': 'DESC'})


def downgrade() -> None:
    op.drop_index('idx_balancing_summary_interval_network_region', table_name='balancing_summary', postgresql_ops={'interval': 'DESC'})
    op.create_index('idx_balancing_summary_interval_network_region', 'balancing_summary', [sa.text('interval DESC'), 'network_id', 'network_region'], unique=False)
    op.drop_index(op.f('ix_at_facility_intervals_unit_code'), table_name='at_facility_intervals')
    op.drop_index(op.f('ix_at_facility_intervals_network_id'), table_name='at_facility_intervals')
    op.drop_index(op.f('ix_at_facility_intervals_facility_code'), table_name='at_facility_intervals')
    op.drop_index('idx_at_facility_intervals_unit_time', table_name='at_facility_intervals')
    op.drop_index('idx_at_facility_intervals_time_facility', table_name='at_facility_intervals')
