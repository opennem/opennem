# pylint: disable=no-member
"""
add network region to at_facility_daily

Revision ID: 1686c3029774
Revises: ce04db068267
Create Date: 2023-03-28 08:54:17.382117

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1686c3029774"
down_revision = "ce04db068267"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "at_facility_daily",
        sa.Column("network_region", sa.Text(), nullable=False),
    )
    op.create_index(
        op.f("ix_at_facility_daily_network_region"),
        "at_facility_daily",
        ["network_region"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_at_facility_daily_network_region"),
        table_name="at_facility_daily",
    )
    op.drop_column("at_facility_daily", "network_region")
