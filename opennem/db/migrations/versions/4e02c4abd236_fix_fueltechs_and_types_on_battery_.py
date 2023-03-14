# pylint: disable=no-member
"""
FIX fueltechs and types on battery facilities

Revision ID: 4e02c4abd236
Revises: c96f1bd608d9
Create Date: 2021-03-29 13:15:27.916004

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "4e02c4abd236"
down_revision = "afdb5be8ac11"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update facility set dispatch_type='LOAD' where fueltech_id='battery_charging'")

    op.execute("update facility set dispatch_type='LOAD', fueltech_id='battery_charging' where code ='LBBL1'")


def downgrade() -> None:
    pass
