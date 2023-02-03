# pylint: disable=no-member
"""
profiler tasks have a level

Revision ID: ab8c24cbc54b
Revises: 4b662d41b962
Create Date: 2023-02-09 17:23:10.705460

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ab8c24cbc54b"
down_revision = "4b662d41b962"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("task_profile", sa.Column("level", sa.Text(), nullable=True))
    op.create_index(op.f("ix_task_profile_level"), "task_profile", ["level"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_task_profile_level"), table_name="task_profile")
    op.drop_column("task_profile", "level")
