# pylint: disable=no-member
"""
victoria big battery name

Revision ID: dce9afc9ca71
Revises: b81295ebb1d7
Create Date: 2022-07-13 00:34:03.524931

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "dce9afc9ca71"
down_revision = "b81295ebb1d7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update station set name = 'Victoria Big Battery' where id=503")


def downgrade() -> None:
    pass
