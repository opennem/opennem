# pylint: disable=no-member
"""
Net interchange on balancing summary per region

Revision ID: 1057033fe1ea
Revises: 405b2ea7b351
Create Date: 2021-01-21 16:45:46.555735

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1057033fe1ea"
down_revision = "405b2ea7b351"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "balancing_summary",
        sa.Column("net_interchange", sa.Numeric(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("balancing_summary", "net_interchange")
