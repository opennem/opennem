# pylint: disable=no-member
"""
indexes on milestone table

Revision ID: aa2d3621ff4b
Revises: 6f4db99fe9b9
Create Date: 2024-08-03 13:09:32.527840

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "aa2d3621ff4b"
down_revision = "6f4db99fe9b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("excl_milestone_record_id_interval", "milestones", ["record_id", "interval"])
    op.create_index("idx_milestone_fueltech_id", "milestones", ["fueltech_id"], unique=False, postgresql_using="btree")
    op.create_index("idx_milestone_network_id", "milestones", ["network_id"], unique=False, postgresql_using="btree")
    op.create_index(op.f("ix_milestones_record_id"), "milestones", ["record_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_milestones_record_id"), table_name="milestones")
    op.drop_index("idx_milestone_network_id", table_name="milestones", postgresql_using="btree")
    op.drop_index("idx_milestone_fueltech_id", table_name="milestones", postgresql_using="btree")
    op.drop_constraint("excl_milestone_record_id_interval", "milestones", type_="unique")
