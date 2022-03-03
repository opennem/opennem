# pylint: disable=no-member
"""
set network_region as part of primary key

Revision ID: 5c41d50dd9b6
Revises: 1f5be71a2af6
Create Date: 2022-03-03 02:22:07.159983

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5c41d50dd9b6"
down_revision = "1f5be71a2af6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE at_network_flows DROP CONSTRAINT at_network_flows_pkey CASCADE")
    op.create_primary_key(
        "at_network_flows_pkey",
        "at_network_flows",
        ["trading_interval", "network_id", "network_region"],
    )


def downgrade() -> None:
    pass
