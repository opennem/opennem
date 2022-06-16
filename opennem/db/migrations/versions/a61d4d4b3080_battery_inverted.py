# pylint: disable=no-member
"""
battery inverted

Revision ID: a61d4d4b3080
Revises: cbb8705b50ac
Create Date: 2022-06-16 05:58:58.130957

"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a61d4d4b3080"
down_revision = "cbb8705b50ac"
branch_labels = None
depends_on = None

battery_charging = """update facility set fueltech_id = 'battery_discharging' where code in (
    'DALNTHL1',
    'BALBL1',
    'GANNBL1',
    'HPRL1',
    'KEPBL1',
    'ADPBA1L',
    'WANDBG1',
    'BULBESL1',
    'VBBL1',
    'WALGRVL1'
)"""

battery_discharging = """update facility set fueltech_id = 'battery_charging' where code in (
    'DALNTH01',
    'BALBG1',
    'GANNBG1',
    'HPRG1',
    'LBBG1',
    'KEPBG1',
    'ADPBA1G',
    'WANDBL1',
    'BULBESG1',
    'VBBG1',
    'WALGRVG1'
)"""


def upgrade() -> None:
    op.execute(battery_charging)
    op.execute(battery_discharging)


def downgrade() -> None:
    pass
