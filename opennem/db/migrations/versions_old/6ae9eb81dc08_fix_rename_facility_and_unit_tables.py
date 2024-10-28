# pylint: disable=no-member
"""
fix: rename facility and unit tables

Revision ID: 6ae9eb81dc08
Revises: 756e3ad139ad
Create Date: 2024-10-24 19:38:07.936749

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6ae9eb81dc08'
down_revision = '756e3ad139ad'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("alter table facility rename to units")
    op.execute("alter table station rename to facilities")


def downgrade() -> None:
    pass
