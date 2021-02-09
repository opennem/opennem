# pylint: disable=no-member
"""
Upate price field

Revision ID: ddb5d2a90896
Revises: 57c6030dcb87
Create Date: 2021-02-10 01:50:27.287152

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ddb5d2a90896"
down_revision = "57c6030dcb87"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "balancing_summary",
        sa.Column("price_dispatch", sa.Numeric(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("balancing_summary", "price_dispatch")
