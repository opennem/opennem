# pylint: disable=no-member
"""
remove foreign indexes on at_facility_daily

Revision ID: 576480e97f8f
Revises: 2ddb804ff7c1
Create Date: 2023-04-13 13:17:11.970837

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "576480e97f8f"
down_revision = "2ddb804ff7c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "fk_at_facility_daily_network_code",
        "at_facility_daily",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_at_facility_daily_facility_code",
        "at_facility_daily",
        type_="foreignkey",
    )


def downgrade() -> None:
    op.create_foreign_key(
        "fk_at_facility_daily_facility_code",
        "at_facility_daily",
        "facility",
        ["facility_code"],
        ["code"],
    )
    op.create_foreign_key(
        "fk_at_facility_daily_network_code",
        "at_facility_daily",
        "network",
        ["network_id"],
        ["code"],
    )
