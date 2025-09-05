# pylint: disable=no-member
"""
remove old unit metadata

Revision ID: 53a383ea9bcc
Revises: 22abee71afa8
Create Date: 2025-09-05 02:02:43.170471

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53a383ea9bcc'
down_revision = '22abee71afa8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(None, 'facilities', ['cms_id'])
    op.drop_index(op.f('idx_unit_history_changed_at'), table_name='unit_history')
    op.drop_index(op.f('idx_unit_history_unit_id'), table_name='unit_history')
    op.create_index(op.f('ix_unit_history_changed_at'), 'unit_history', ['changed_at'], unique=False)
    op.create_index(op.f('ix_unit_history_unit_id'), 'unit_history', ['unit_id'], unique=False)
    op.alter_column('units', 'emissions_factor_co2',
               existing_type=sa.NUMERIC(precision=16, scale=4),
               type_=sa.Numeric(precision=20, scale=6),
               existing_nullable=True)
    op.create_unique_constraint(None, 'units', ['cms_id'])
    op.drop_column('units', 'unit_alias')
    op.drop_column('units', 'unit_id')
    op.drop_column('units', 'unit_number')
    op.drop_column('units', 'unit_capacity')


def downgrade() -> None:
    op.add_column('units', sa.Column('unit_capacity', sa.NUMERIC(), autoincrement=False, nullable=True))
    op.add_column('units', sa.Column('unit_number', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('units', sa.Column('unit_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('units', sa.Column('unit_alias', sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'units', type_='unique')
    op.alter_column('units', 'emissions_factor_co2',
               existing_type=sa.Numeric(precision=20, scale=6),
               type_=sa.NUMERIC(precision=16, scale=4),
               existing_nullable=True)
    op.drop_index(op.f('ix_unit_history_unit_id'), table_name='unit_history')
    op.drop_index(op.f('ix_unit_history_changed_at'), table_name='unit_history')
    op.create_index(op.f('idx_unit_history_unit_id'), 'unit_history', ['unit_id'], unique=False)
    op.create_index(op.f('idx_unit_history_changed_at'), 'unit_history', ['changed_at'], unique=False)
    op.drop_constraint(None, 'facilities', type_='unique')
