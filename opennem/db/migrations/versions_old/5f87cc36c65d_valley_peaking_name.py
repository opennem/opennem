# pylint: disable=no-member
"""
valley peaking name

Revision ID: 5f87cc36c65d
Revises: dce9afc9ca71
Create Date: 2022-07-13 00:36:13.819254

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "5f87cc36c65d"
down_revision = "dce9afc9ca71"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update station set name = 'Valley Peaking' where id=321")


def downgrade() -> None:
    pass
