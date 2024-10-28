# pylint: disable=no-member
"""
move crookwell 3

Revision ID: fdb4c6c60e8f
Revises: 9b7c579cf297
Create Date: 2024-07-23 09:21:39.908073

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = "fdb4c6c60e8f"
down_revision = "9b7c579cf297"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # delete crookwell 3 since we're moving it
    op.execute("delete from facility where code='CROOKWF3'")


def downgrade() -> None:
    pass
