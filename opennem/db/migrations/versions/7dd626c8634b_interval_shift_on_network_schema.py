# pylint: disable=no-member
"""
interval_shift on network schema

Revision ID: 7dd626c8634b
Revises: 4e02c4abd236
Create Date: 2021-04-09 10:53:00.992763

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7dd626c8634b"
down_revision = "4e02c4abd236"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("network", sa.Column("interval_shift", sa.Integer(), nullable=True))
    op.execute("UPDATE network SET interval_shift = 0")
    op.alter_column("network", "interval_shift", nullable=False)

    op.add_column("network", sa.Column("network_price", sa.Text(), nullable=True))
    op.execute("update network set network_price='NEM';")
    op.alter_column("network", "interval_shift", nullable=False)


def downgrade() -> None:
    op.drop_column("network", "interval_shift")
    op.drop_column("network", "network_price")
