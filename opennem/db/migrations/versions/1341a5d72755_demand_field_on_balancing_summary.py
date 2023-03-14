# pylint: disable=no-member
"""
demand field on balancing_summary

Revision ID: 1341a5d72755
Revises: f6f4398975ed
Create Date: 2022-08-10 08:13:57.897935

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "1341a5d72755"
down_revision = "f6f4398975ed"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("balancing_summary", sa.Column("demand", sa.Numeric(), nullable=True))


def downgrade() -> None:
    op.drop_column("balancing_summary", "demand")
