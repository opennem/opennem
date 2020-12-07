# pylint: disable=no-member
"""
Fix APVI scada records to have network APVI

Revision ID: 467a3223b204
Revises: bfb98983b92c
Create Date: 2020-12-07 16:37:00.632028

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "467a3223b204"
down_revision = "bfb98983b92c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "delete from facility_scada where network_id='NEM' and facility_code like 'ROOFTOP_APVI_%'"
    )


def downgrade() -> None:
    pass
