# pylint: disable=no-member
"""
make timezone interval field

Revision ID: 6f4db99fe9b9
Revises: b207a3b6c080
Create Date: 2024-08-03 12:52:29.154115

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6f4db99fe9b9"
down_revision = "b207a3b6c080"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "milestones",
        "interval",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.DateTime(timezone=True),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "milestones",
        "interval",
        existing_type=sa.DateTime(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=False,
    )
