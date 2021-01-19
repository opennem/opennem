# pylint: disable=no-member
"""
Remove mv_network_energy_hour

Revision ID: 9c7482a0fc9a
Revises: 977f219c8563
Create Date: 2021-01-19 16:19:01.151500

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "9c7482a0fc9a"
down_revision = "977f219c8563"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("drop view if exists mv_network_energy_hour cascade;")


def downgrade() -> None:
    pass
