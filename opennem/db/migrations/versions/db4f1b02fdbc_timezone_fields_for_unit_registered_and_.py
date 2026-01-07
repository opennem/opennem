# pylint: disable=no-member
"""
timezone fields for unit registered and deregistered

Revision ID: db4f1b02fdbc
Revises: e8c592a9c53a
Create Date: 2025-09-24 05:56:51.128579

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'db4f1b02fdbc'
down_revision = 'e8c592a9c53a'
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.alter_column('units', 'registered',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)
    op.alter_column('units', 'deregistered',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('units', 'deregistered',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
    op.alter_column('units', 'registered',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
