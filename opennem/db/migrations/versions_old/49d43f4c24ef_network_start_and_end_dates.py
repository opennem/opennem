# pylint: disable=no-member
"""
network start and end dates

Revision ID: 49d43f4c24ef
Revises: c860e4328b38
Create Date: 2022-06-23 23:59:25.454223

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "49d43f4c24ef"
down_revision = "c860e4328b38"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "network",
        sa.Column(
            "data_start_date",
            postgresql.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "network",
        sa.Column("data_end_date", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index(
        op.f("ix_network_data_end_date"),
        "network",
        ["data_end_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_network_data_start_date"),
        "network",
        ["data_start_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_network_data_start_date"), table_name="network")
    op.drop_index(op.f("ix_network_data_end_date"), table_name="network")
    op.drop_column("network", "data_end_date")
    op.drop_column("network", "data_start_date")
