# pylint: disable=no-member
"""
facility station id index

Revision ID: 331d237fa740
Revises: 166fa429decd
Create Date: 2023-05-09 13:25:39.950578

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "331d237fa740"
down_revision = "166fa429decd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("idx_facility_station_id", "facility", ["station_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_facility_station_id", table_name="facility")
