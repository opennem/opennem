# pylint: disable=no-member
"""
rename milesones dtime to interval

Revision ID: 8e4fb8e5135a
Revises: 13e1d4bdf9c1
Create Date: 2024-02-14 13:06:21.168993

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8e4fb8e5135a"
down_revision = "13e1d4bdf9c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "milestones",
        sa.Column("instance_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interval", sa.DateTime(timezone=False), nullable=False),
        sa.Column(
            "record_type",
            sa.Enum("low", "average", "high", name="milestonetype"),
            nullable=False,
        ),
        sa.Column("significance", sa.Integer(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("facility_id", sa.Text(), nullable=True),
        sa.Column("network_id", sa.String(), nullable=True),
        sa.Column("fueltech_id", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["fueltech_id"],
            ["fueltech.code"],
        ),
        sa.ForeignKeyConstraint(
            ["network_id"],
            ["network.code"],
        ),
        sa.PrimaryKeyConstraint("instance_id", "record_id"),
    )
    op.create_index(
        op.f("ix_milestones_interval"),
        "milestones",
        ["interval"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("milestones")
