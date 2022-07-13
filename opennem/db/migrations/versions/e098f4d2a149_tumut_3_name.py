# pylint: disable=no-member
"""
tumut 3 name

Revision ID: e098f4d2a149
Revises: 5f87cc36c65d
Create Date: 2022-07-13 00:39:30.342945

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "e098f4d2a149"
down_revision = "5f87cc36c65d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update station set name='Tumut 3' where id=277")


def downgrade() -> None:
    pass
