# pylint: disable=no-member
"""
Data fix price data

Revision ID: 156aec569e8d
Revises: a6261453b8e7
Create Date: 2021-01-31 00:11:27.874617

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "156aec569e8d"
down_revision = "a6261453b8e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update balancing_summary set price=NULL where network_id='NEM';")


def downgrade() -> None:
    pass
