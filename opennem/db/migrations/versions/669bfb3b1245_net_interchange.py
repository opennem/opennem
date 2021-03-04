# pylint: disable=no-member
"""
net interchange

Revision ID: 669bfb3b1245
Revises: 3afcf7bf755c
Create Date: 2021-03-05 04:29:17.113967

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "669bfb3b1245"
down_revision = "3afcf7bf755c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "balancing_summary",
        sa.Column("net_interchange_trading", sa.Numeric(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("balancing_summary", "net_interchange_trading")
