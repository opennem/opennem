# pylint: disable=no-member
"""
remove old energy field

Revision ID: 2f6d8cb5bcdf
Revises: 98da390bf8fc
Create Date: 2024-11-12 15:50:21.431633

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f6d8cb5bcdf'
down_revision = '98da390bf8fc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index('idx_facility_scada_group', table_name='facility_scada')
    op.create_index('idx_facility_scada_grouping', 'facility_scada', ['network_id', 'facility_code', 'energy'], unique=False, postgresql_using='btree')
    op.drop_column('facility_scada', 'eoi_quantity')


def downgrade() -> None:
    op.add_column('facility_scada', sa.Column('eoi_quantity', sa.NUMERIC(), autoincrement=False, nullable=True))
    op.drop_index('idx_facility_scada_grouping', table_name='facility_scada', postgresql_using='btree')
    op.create_index('idx_facility_scada_group', 'facility_scada', ['network_id', 'facility_code', 'generated', 'energy'], unique=False)
