# pylint: disable=no-member
"""
profiled tasks have a retention period

Revision ID: 4b662d41b962
Revises: b45656659882
Create Date: 2023-02-09 16:26:20.837463

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4b662d41b962"
down_revision = "b45656659882"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("task_profile", sa.Column("retention_period", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix_task_profile_retention_period"),
        "task_profile",
        ["retention_period"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_task_profile_retention_period"), table_name="task_profile")
    op.drop_column("task_profile", "retention_period")
