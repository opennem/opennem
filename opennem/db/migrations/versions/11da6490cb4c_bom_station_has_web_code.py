# pylint: disable=no-member
"""
bom station has web code

Revision ID: 11da6490cb4c
Revises: 2d02f3cbd62a
Create Date: 2021-10-14 07:47:40.983935

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '11da6490cb4c'
down_revision = '2d02f3cbd62a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('bom_station', sa.Column('web_code', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('bom_station', 'web_code')
