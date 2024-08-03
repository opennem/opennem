# pylint: disable=no-member
"""
milestones table rename to previous_instance_id

Revision ID: 367148d1eb47
Revises: aa2d3621ff4b
Create Date: 2024-08-03 15:08:21.237576

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = "367148d1eb47"
down_revision = "aa2d3621ff4b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("milestones", sa.Column("previous_instance_id", sa.UUID(), nullable=True))
    op.drop_column("milestones", "previous_record_id")


def downgrade() -> None:
    op.add_column("milestones", sa.Column("previous_record_id", sa.TEXT(), autoincrement=False, nullable=True))
    op.drop_column("milestones", "previous_instance_id")
