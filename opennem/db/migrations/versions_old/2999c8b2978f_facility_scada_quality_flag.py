# pylint: disable=no-member
"""
Facility scada quality flag

Revision ID: 2999c8b2978f
Revises: ebdfa7a4627b
Create Date: 2021-03-17 15:04:06.540805

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2999c8b2978f"
down_revision = "ebdfa7a4627b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "facility_scada",
        sa.Column("energy_quality_flag", sa.Numeric(), nullable=True),
    )
    op.execute("UPDATE facility_scada SET energy_quality_flag = 0")
    op.alter_column("facility_scada", "energy_quality_flag", nullable=False)


def downgrade() -> None:
    op.drop_column("facility_scada", "energy_quality_flag")
