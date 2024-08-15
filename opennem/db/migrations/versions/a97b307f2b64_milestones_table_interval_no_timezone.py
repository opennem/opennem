# pylint: disable=no-member
"""
milestones table interval no timezone

Revision ID: a97b307f2b64
Revises: 1b260c6a31f4
Create Date: 2024-08-16 01:25:43.132965

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a97b307f2b64"
down_revision = "1b260c6a31f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "milestones",
        "interval",
        existing_type=postgresql.TIMESTAMP(timezone=True),
        type_=sa.DateTime(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "milestones",
        "interval",
        existing_type=sa.DateTime(),
        type_=postgresql.TIMESTAMP(timezone=True),
        existing_nullable=False,
    )
