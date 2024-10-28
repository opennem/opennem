# pylint: disable=no-member
"""
milestone table region rename

Revision ID: 615d07cea9ec
Revises: d0931b69b37f
Create Date: 2023-12-12 08:29:21.288664

"""
from alembic import op
import sqlalchemy as sa


revision = "615d07cea9ec"
down_revision = "d0931b69b37f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("milestones", sa.Column("network_region", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("milestones", "network_region")
