# pylint: disable=no-member
"""
remove erronous bango facility

Revision ID: 166fa429decd
Revises: ff058d34cd31
Create Date: 2023-05-08 12:48:38.183391

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "166fa429decd"
down_revision = "ff058d34cd31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # bad bango facility
    op.execute("delete from facility where id=691")


def downgrade() -> None:
    pass
