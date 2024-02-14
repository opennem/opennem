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
    op.alter_column("milestones", "dtime", new_column_name="interval", new_type=sa.DateTime(timezone=True))
    op.add_column(
        "milestones",
        sa.Column("interval", sa.DateTime(timezone=True), nullable=False),
    )
    op.drop_index("ix_milestones_dtime", table_name="milestones")
    op.create_index(
        op.f("ix_milestones_interval"),
        "milestones",
        ["interval"],
        unique=False,
    )


def downgrade() -> None:
    op.alter_column("milestones", "interval", new_column_name="dtime", new_type=sa.DateTime(timezone=True))
    op.drop_index(op.f("ix_milestones_interval"), table_name="milestones")
    op.create_index(
        "ix_milestones_dtime", "milestones", ["dtime"], unique=False
    )
    op.drop_column("milestones", "interval")
