# pylint: disable=no-member
"""
Update fueltechs

Revision ID: fcb509301bda
Revises: 6e45ee9557c2
Create Date: 2021-02-04 10:41:38.122003

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "fcb509301bda"
down_revision = "6e45ee9557c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update facility set fueltech_id='battery_discharging' where code IN ('LBBL1')")


def downgrade() -> None:
    pass
