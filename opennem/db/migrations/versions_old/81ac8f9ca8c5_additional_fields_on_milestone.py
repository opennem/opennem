# pylint: disable=no-member
"""
additional fields on milestone

Revision ID: 81ac8f9ca8c5
Revises: fdb4c6c60e8f
Create Date: 2024-08-01 10:42:42.648994

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "81ac8f9ca8c5"
down_revision = "fdb4c6c60e8f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("milestones", sa.Column("record_field", sa.String(), nullable=True))
    op.add_column("milestones", sa.Column("previous_record_id", sa.Text(), nullable=True))



def downgrade() -> None:
    op.drop_column("milestones", "previous_record_id")
    op.drop_column("milestones", "record_field")
