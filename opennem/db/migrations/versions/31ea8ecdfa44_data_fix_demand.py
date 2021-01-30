# pylint: disable=no-member
"""
Data fix demand

Revision ID: 31ea8ecdfa44
Revises: 156aec569e8d
Create Date: 2021-01-31 00:28:35.164479

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "31ea8ecdfa44"
down_revision = "156aec569e8d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update balancing_summary set demand_total=NULL where network_id='NEM';")


def downgrade() -> None:
    pass
