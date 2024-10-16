# pylint: disable=no-member
"""
dispatch_type type to string

Revision ID: 441113b529a5
Revises: 9ae9d41678e7
Create Date: 2024-10-21 19:42:31.607727

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '441113b529a5'
down_revision = '9ae9d41678e7'
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.alter_column('facility', 'dispatch_type',
               existing_type=postgresql.ENUM('GENERATOR', 'LOAD', 'BIDIRECTIONAL', name='dispatch_type'),
               type_=sa.Text(),
               existing_nullable=False)


def downgrade() -> None:
    op.alter_column('facility', 'dispatch_type',
               existing_type=sa.Text(),
               type_=postgresql.ENUM('GENERATOR', 'LOAD', 'BIDIRECTIONAL', name='dispatch_type'),
               existing_nullable=False)
