# pylint: disable=no-member
"""
Darling Downs capacity fix

Revision ID: 4508f80f7f9f
Revises: 21f32dd12775
Create Date: 2021-05-03 11:14:57.444352

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "4508f80f7f9f"
down_revision = "21f32dd12775"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update facility set capacity_registered=644 where code='DDPS1'")


def downgrade() -> None:
    pass
