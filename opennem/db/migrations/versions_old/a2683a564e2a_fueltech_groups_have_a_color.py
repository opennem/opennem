# pylint: disable=no-member
"""
fueltech groups have a color

Revision ID: a2683a564e2a
Revises: 1f1f506e4d44
Create Date: 2022-09-23 09:52:24.723579

"""
import sqlalchemy as sa
from alembic import op

revision = "a2683a564e2a"
down_revision = "1f1f506e4d44"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fueltech_group", sa.Column("color", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("fueltech_group", "color")
