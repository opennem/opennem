# pylint: disable=no-member
"""
period field on milestones

Revision ID: 1485ce197dbd
Revises: 8e4fb8e5135a
Create Date: 2024-02-15 09:54:53.144810

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1485ce197dbd"
down_revision = "8e4fb8e5135a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("milestones", sa.Column("period", sa.String(), nullable=True))



def downgrade() -> None:
    op.drop_column("milestones", "period")
