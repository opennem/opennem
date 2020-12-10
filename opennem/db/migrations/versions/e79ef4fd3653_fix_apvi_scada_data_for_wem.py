# pylint: disable=no-member
"""
Fix APVI scada data for WEM

Revision ID: e79ef4fd3653
Revises: 72a817116434
Create Date: 2020-12-10 18:12:59.851256

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "e79ef4fd3653"
down_revision = "72a817116434"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "delete from facility_scada where facility_code = 'ROOFTOP_APVI_WA' and network_id='WEM'"
    )


def downgrade() -> None:
    pass
