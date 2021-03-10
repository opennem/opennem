# pylint: disable=no-member
"""
Add order and primary to photos model

Revision ID: fc245eb205ed
Revises: 31b16536ac2e
Create Date: 2021-03-10 14:35:06.058918

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fc245eb205ed"
down_revision = "31b16536ac2e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("photo", sa.Column("is_primary", sa.Boolean(), nullable=True))
    op.add_column("photo", sa.Column("order", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("photo", "order")
    op.drop_column("photo", "is_primary")
