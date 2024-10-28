# pylint: disable=no-member
"""
interconnector region from

Revision ID: 32ab251e2170
Revises: 11da6490cb4c
Create Date: 2021-10-21 03:08:08.783314

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "32ab251e2170"
down_revision = "11da6490cb4c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("facility", sa.Column("interconnector_region_from", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix_facility_interconnector_region_from"),
        "facility",
        ["interconnector_region_from"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_facility_interconnector_region_from"), table_name="facility")
    op.drop_column("facility", "interconnector_region_from")
