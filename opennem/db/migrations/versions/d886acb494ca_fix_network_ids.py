# pylint: disable=no-member
"""
Fix network ids

Revision ID: d886acb494ca
Revises: eeb81f56767e
Create Date: 2020-11-24 11:48:22.720354

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d886acb494ca"
down_revision = "eeb81f56767e"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "update facility set network_id='NEM' where network_region in ('NSW1', 'QLD1', 'SA1', 'TAS1', 'VIC1')"
    )
    op.execute(
        "update facility set network_id='WEM' where network_region in ('WEM')"
    )


def downgrade():
    pass
