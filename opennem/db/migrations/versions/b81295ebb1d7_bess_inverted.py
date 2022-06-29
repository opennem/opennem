# pylint: disable=no-member
"""
bess inverted

Revision ID: b81295ebb1d7
Revises: 49d43f4c24ef
Create Date: 2022-07-03 02:16:07.858589

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b81295ebb1d7"
down_revision = "49d43f4c24ef"
branch_labels = None
depends_on = None


battery_charging = """update facility set fueltech_id = 'battery_discharging' where code in (
    'WANDBL1'
)"""

battery_discharging = """update facility set fueltech_id = 'battery_charging' where code in (
    'WANDBG1'
)"""


def upgrade() -> None:
    op.execute(battery_charging)
    op.execute(battery_discharging)


def downgrade() -> None:
    pass
