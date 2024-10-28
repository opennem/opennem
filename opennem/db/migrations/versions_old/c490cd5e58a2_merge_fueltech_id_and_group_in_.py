# pylint: disable=no-member
"""
merge fueltech_id and group in milestones

Revision ID: c490cd5e58a2
Revises: 93332631773a
Create Date: 2024-08-08 22:06:42.088891

"""
from alembic import op
import sqlalchemy as sa


revision = "c490cd5e58a2"
down_revision = "93332631773a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("milestones_fueltech_group_id_fkey", "milestones", type_="foreignkey")
    op.drop_constraint("milestones_fueltech_id_fkey", "milestones", type_="foreignkey")
    op.drop_column("milestones", "fueltech_group_id")


def downgrade() -> None:
    op.add_column("milestones", sa.Column("fueltech_group_id", sa.TEXT(), autoincrement=False, nullable=True))
    op.create_foreign_key("milestones_fueltech_id_fkey", "milestones", "fueltech", ["fueltech_id"], ["code"])
    op.create_foreign_key(
        "milestones_fueltech_group_id_fkey", "milestones", "fueltech_group", ["fueltech_group_id"], ["code"]
    )
