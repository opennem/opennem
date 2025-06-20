# pylint: disable=no-member
"""
unit and facility table extra fields and cms_id

Revision ID: 74e78ac98245
Revises: 4ae275627ed5
Create Date: 2025-06-20 03:22:10.621521

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '74e78ac98245'
down_revision = '4ae275627ed5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('facilities', sa.Column('cms_id', sa.UUID(), nullable=True))
    op.add_column('units', sa.Column('commencement_date', sa.DateTime(), nullable=True))
    op.add_column('units', sa.Column('closure_date', sa.DateTime(), nullable=True))
    op.add_column('units', sa.Column('expected_operation_date', sa.DateTime(), nullable=True))
    op.add_column('units', sa.Column('cms_id', sa.UUID(), nullable=True))


def downgrade() -> None:
    op.drop_column('units', 'cms_id')
    op.drop_column('units', 'expected_operation_date')
    op.drop_column('units', 'closure_date')
    op.drop_column('units', 'commencement_date')
    op.drop_column('facilities', 'cms_id')
