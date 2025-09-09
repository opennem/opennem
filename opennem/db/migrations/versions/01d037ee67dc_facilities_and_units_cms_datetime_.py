# pylint: disable=no-member
"""
facilities and units cms datetime metadata

Revision ID: 01d037ee67dc
Revises: cb7207833fbd
Create Date: 2025-09-08 23:55:17.495198

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '01d037ee67dc'
down_revision = 'cb7207833fbd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('facilities', sa.Column('cms_created_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('facilities', sa.Column('cms_updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('units', sa.Column('cms_created_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('units', sa.Column('cms_updated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('units', 'cms_updated_at')
    op.drop_column('units', 'cms_created_at')
    op.drop_column('facilities', 'cms_updated_at')
    op.drop_column('facilities', 'cms_created_at')
