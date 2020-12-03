# pylint: disable=no-member
"""
Facility scada network index

Revision ID: bfb98983b92c
Revises: ee93cbe26f74
Create Date: 2020-12-03 06:05:10.081580

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "bfb98983b92c"
down_revision = "ee93cbe26f74"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "create index if not exists idx_facility_scada_network_id on facility_scada  (network_id)"
    )


def downgrade() -> None:
    op.execute("drop index idx_facility_scada_network_id")
