# pylint: disable=no-member
"""
Interconnector metadata on facility

Revision ID: 000e7fdab7e2
Revises: 8746bdb27550
Create Date: 2020-12-24 15:01:38.583540

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "000e7fdab7e2"
down_revision = "8746bdb27550"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "facility", sa.Column("interconnector", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "facility",
        sa.Column("interconnector_region_to", sa.Text(), nullable=True),
    )
    op.create_index(
        op.f("ix_facility_interconnector"),
        "facility",
        ["interconnector"],
        unique=False,
    )
    op.create_index(
        op.f("ix_facility_interconnector_region_to"),
        "facility",
        ["interconnector_region_to"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_facility_interconnector_region_to"), table_name="facility"
    )
    op.drop_index(op.f("ix_facility_interconnector"), table_name="facility")
    op.drop_column("facility", "interconnector_region_to")
    op.drop_column("facility", "interconnector")
