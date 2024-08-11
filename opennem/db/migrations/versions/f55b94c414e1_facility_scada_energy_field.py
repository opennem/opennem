# pylint: disable=no-member
"""
facility_scada energy field

Revision ID: f55b94c414e1
Revises: da1708083f49
Create Date: 2024-08-11 13:03:30.709399

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = "f55b94c414e1"
down_revision = "da1708083f49"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("facility_scada", sa.Column("energy", sa.Numeric(), nullable=True))



def downgrade() -> None:
    op.drop_column("facility_scada", "energy")
