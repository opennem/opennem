# pylint: disable=no-member
"""
update Barcaldine solar farm capacity

Revision ID: 57c6030dcb87
Revises: fcb509301bda
Create Date: 2021-02-09 23:29:05.629873

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "57c6030dcb87"
down_revision = "fcb509301bda"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update facility set capacity_registered=20 where code='BARCSF1';")


def downgrade() -> None:
    pass
