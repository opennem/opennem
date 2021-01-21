# pylint: disable=no-member
"""
Total demand on balancing summary per region

Revision ID: d130be833a0c
Revises: 1057033fe1ea
Create Date: 2021-01-21 16:54:01.264342

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d130be833a0c"
down_revision = "1057033fe1ea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "balancing_summary",
        sa.Column("demand_total", sa.Numeric(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("balancing_summary", "demand_total")
