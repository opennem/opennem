# pylint: disable=no-member
"""
Add metadata fields to at_network_flows

Revision ID: 1f5be71a2af6
Revises: 109f0ddd92ad
Create Date: 2022-03-03 02:15:39.940049

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1f5be71a2af6"
down_revision = "109f0ddd92ad"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("at_network_flows", sa.Column("created_by", sa.Text(), nullable=True))
    op.add_column(
        "at_network_flows",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    op.add_column(
        "at_network_flows",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("at_network_flows", "updated_at")
    op.drop_column("at_network_flows", "created_at")
    op.drop_column("at_network_flows", "created_by")
