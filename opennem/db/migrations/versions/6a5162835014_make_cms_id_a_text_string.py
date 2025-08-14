# pylint: disable=no-member
"""
make cms_id a text string

Revision ID: 6a5162835014
Revises: 74e78ac98245
Create Date: 2025-06-20 03:52:02.871514

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = '6a5162835014'
down_revision = '74e78ac98245'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('facilities', 'cms_id',
               existing_type=sa.UUID(),
               type_=sa.Text(),
               existing_nullable=True)
    op.alter_column('units', 'cms_id',
               existing_type=sa.UUID(),
               type_=sa.Text(),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('units', 'cms_id',
               existing_type=sa.Text(),
               type_=sa.UUID(),
               existing_nullable=True)
    op.alter_column('facilities', 'cms_id',
               existing_type=sa.Text(),
               type_=sa.UUID(),
               existing_nullable=True)
