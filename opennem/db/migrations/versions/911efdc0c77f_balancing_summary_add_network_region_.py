# pylint: disable=no-member
"""Balancing summary add network_region column

Revision ID: 911efdc0c77f
Revises: 8bf30c37cb85
Create Date: 2020-10-07 11:16:51.578193

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "911efdc0c77f"
down_revision = "8bf30c37cb85"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "balancing_summary",
        sa.Column("network_region", sa.Text(), nullable=True),
    )
    op.execute("COMMIT")
    op.execute(
        "update balancing_summary set network_region='WEM' where network_id='WEM'"
    )


def downgrade():
    op.drop_column("balancing_summary", "network_region")
