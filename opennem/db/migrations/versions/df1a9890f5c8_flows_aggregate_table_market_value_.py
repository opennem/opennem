# pylint: disable=no-member
"""
flows aggregate table market value fields

Revision ID: df1a9890f5c8
Revises: 32ab251e2170
Create Date: 2021-11-02 03:01:28.785544

"""
import sqlalchemy as sa
from alembic import op

revision = "df1a9890f5c8"
down_revision = "32ab251e2170"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "at_network_flows",
        sa.Column("market_value_imports", sa.Numeric(), nullable=True),
    )
    op.add_column(
        "at_network_flows",
        sa.Column("market_value_exports", sa.Numeric(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("at_network_flows", "market_value_exports")
    op.drop_column("at_network_flows", "market_value_imports")
