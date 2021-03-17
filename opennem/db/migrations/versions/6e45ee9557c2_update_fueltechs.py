# pylint: disable=no-member
"""
Update capacity registered for BARCSF1

Revision ID: 6e45ee9557c2
Revises: b2c0f8c9d5db
Create Date: 2021-02-02 16:16:37.583127

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "6e45ee9557c2"
down_revision = "c203c9207aa3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update facility set capacity_registered=20 where code='BARCSF1';")


def downgrade() -> None:
    pass
