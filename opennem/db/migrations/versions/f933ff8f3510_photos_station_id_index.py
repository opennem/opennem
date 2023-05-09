# pylint: disable=no-member
"""
photos station_id index

Revision ID: f933ff8f3510
Revises: 40b7b3ffb0cc
Create Date: 2023-05-09 13:32:55.955160

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "f933ff8f3510"
down_revision = "40b7b3ffb0cc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_photo_station_id",
        "photo",
        ["station_id"],
        unique=False,
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index("idx_photo_station_id", table_name="photo", postgresql_using="btree")
