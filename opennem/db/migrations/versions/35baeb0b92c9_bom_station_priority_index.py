# pylint: disable=no-member
"""
bom station priority index

Revision ID: 35baeb0b92c9
Revises: 331d237fa740
Create Date: 2023-05-09 13:27:48.474690

"""
from alembic import op

revision = "35baeb0b92c9"
down_revision = "331d237fa740"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_bom_station_priority",
        "bom_station",
        ["priority"],
        unique=False,
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index(
        "idx_bom_station_priority",
        table_name="bom_station",
        postgresql_using="btree",
    )
