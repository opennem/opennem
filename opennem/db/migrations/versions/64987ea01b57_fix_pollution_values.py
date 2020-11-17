# pylint: disable=no-member
"""
Fix pollution values

Revision ID: 64987ea01b57
Revises: 10f179b31ef8
Create Date: 2020-11-17 18:34:20.197091

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "64987ea01b57"
down_revision = "10f179b31ef8"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "update facility set emissions_factor_co2 = NULL where network_id='WEM'"
    )


def downgrade():
    pass
