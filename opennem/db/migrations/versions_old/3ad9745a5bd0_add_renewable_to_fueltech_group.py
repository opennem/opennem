# pylint: disable=no-member
"""
add renewable to fueltech group

Revision ID: 3ad9745a5bd0
Revises: 99d1cadc9655
Create Date: 2024-08-13 12:49:34.934800

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3ad9745a5bd0"
down_revision = "99d1cadc9655"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fueltech_group", sa.Column("renewable", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("fueltech_group", "renewable")
