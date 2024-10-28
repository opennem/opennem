# pylint: disable=no-member
"""
migrate wem data to wemde

Revision ID: cbdfea6ca557
Revises: f55b94c414e1
Create Date: 2024-08-12 01:19:42.077535

"""
from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision = "cbdfea6ca557"
down_revision = "f55b94c414e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update facility_scada set network_id='WEMDE' where network_id='WEM' and interval >= '2023-10-01 08:00:00'")
    op.execute("update balancing_summary set network_id='WEMDE', network_region='WEMDE' where network_id = 'WEM' and interval >= '2023-10-01 08:00:00'")


def downgrade() -> None:
    pass
