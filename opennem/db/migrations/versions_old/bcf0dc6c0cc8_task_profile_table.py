# pylint: disable=no-member
"""
task profile table

Revision ID: bcf0dc6c0cc8
Revises: 0cabef36e666
Create Date: 2022-12-09 09:48:36.793311

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "bcf0dc6c0cc8"
down_revision = "0cabef36e666"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_name", sa.Text(), nullable=False),
        sa.Column("time_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_sql", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_cpu", sa.DateTime(timezone=True), nullable=True),
        sa.Column("errors", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("task_profile")
