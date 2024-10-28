# pylint: disable=no-member
"""
invokee name on task profile

Revision ID: 9765ef882492
Revises: ab8c24cbc54b
Create Date: 2023-02-17 10:52:41.079963

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9765ef882492"
down_revision = "ab8c24cbc54b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("task_profile", sa.Column("invokee_name", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix_task_profile_invokee_name"),
        "task_profile",
        ["invokee_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_task_profile_invokee_name"), table_name="task_profile")
    op.drop_column("task_profile", "invokee_name")
