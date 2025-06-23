# pylint: disable=no-member
"""
add unit history table

Revision ID: 07e436912603
Revises: 74e78ac98245
Create Date: 2025-01-03 15:21:59.890916

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '07e436912603'
down_revision = '74e78ac98245'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Create unit_history table for tracking changes to unit fields over time.
    """
    # Create unit_history table
    op.create_table('unit_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('unit_id', sa.Integer(), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('changed_by', sa.Text(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('capacity_registered', sa.Numeric(), nullable=True),
        sa.Column('emissions_factor_co2', sa.Numeric(precision=20, scale=6), nullable=True),
        sa.Column('emission_factor_source', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['unit_id'], ['units.id'], name='fk_unit_history_unit_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_unit_history_unit_id', 'unit_history', ['unit_id'], unique=False)
    op.create_index('idx_unit_history_changed_at', 'unit_history', ['changed_at'], unique=False)
    op.create_index('idx_unit_history_unit_id_changed_at', 'unit_history', ['unit_id', 'changed_at'], unique=False)



def downgrade() -> None:
    """
    Drop unit_history table and indexes.
    """
    # Drop indexes first
    op.drop_index('idx_unit_history_unit_id_changed_at', table_name='unit_history')
    op.drop_index('idx_unit_history_changed_at', table_name='unit_history')
    op.drop_index('idx_unit_history_unit_id', table_name='unit_history')

    # Drop the table
    op.drop_table('unit_history')
