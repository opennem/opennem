# pylint: disable=no-member
"""
Network network price sync revision

Revision ID: 77bf497fb398
Revises: efb63b1a723d
Create Date: 2021-05-26 15:05:01.051318

"""
import sqlalchemy as sa
from alembic import op

revision = "77bf497fb398"
down_revision = "efb63b1a723d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("network", "network_price", existing_type=sa.TEXT(), nullable=False)


def downgrade() -> None:
    op.alter_column("network", "network_price", existing_type=sa.TEXT(), nullable=True)
