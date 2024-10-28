# pylint: disable=no-member
"""
remove created, updated and created_by meta fields on at_network_flows

Revision ID: 60f042e69758
Revises: f933ff8f3510
Create Date: 2023-07-04 08:09:37.699346

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

revision = "60f042e69758"
down_revision = "f933ff8f3510"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("at_network_flows", "updated_at")
    op.drop_column("at_network_flows", "created_by")
    op.drop_column("at_network_flows", "created_at")


def downgrade() -> None:
    op.add_column(
        "at_network_flows",
        sa.Column(
            "created_at",
            postgresql.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "at_network_flows",
        sa.Column("created_by", sa.TEXT(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "at_network_flows",
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMP(timezone=True),
            autoincrement=False,
            nullable=True,
        ),
    )
