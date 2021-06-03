# pylint: disable=no-member
"""
Change feedback user meta fields

Revision ID: 1c1004a2c283
Revises: a65022a04846
Create Date: 2021-06-03 06:23:12.822822

"""
import sqlalchemy as sa
from alembic import op

revision = "1c1004a2c283"
down_revision = "a65022a04846"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("feedback", "user_ip", existing_type=sa.TEXT(), nullable=True)
    op.alter_column("feedback", "user_agent", existing_type=sa.TEXT(), nullable=True)


def downgrade() -> None:
    op.alter_column("feedback", "user_agent", existing_type=sa.TEXT(), nullable=False)
    op.alter_column("feedback", "user_ip", existing_type=sa.TEXT(), nullable=False)
