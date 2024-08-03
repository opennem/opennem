# pylint: disable=no-member
"""
include_in_geojson field on facility

Revision ID: 93332631773a
Revises: 367148d1eb47
Create Date: 2024-08-03 15:56:54.914845

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "93332631773a"
down_revision = "367148d1eb47"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("facility", sa.Column("include_in_geojson", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("facility", "include_in_geojson")
