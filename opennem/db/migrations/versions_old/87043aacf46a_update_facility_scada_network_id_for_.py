# pylint: disable=no-member
"""
Update facility scada network id for rooftop

Revision ID: 87043aacf46a
Revises: 7dd626c8634b
Create Date: 2021-04-09 11:57:05.604227

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "87043aacf46a"
down_revision = "7dd626c8634b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update facility_scada set network_id='AEMO_ROOFTOP' where facility_code like 'ROOFTOP_NEM_%';")


def downgrade() -> None:
    pass
