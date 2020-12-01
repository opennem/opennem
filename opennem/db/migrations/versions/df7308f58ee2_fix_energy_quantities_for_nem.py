# pylint: disable=no-member
"""
Fix energy quantities for NEM

Revision ID: df7308f58ee2
Revises: d886acb494ca
Create Date: 2020-12-02 01:53:38.801723

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "df7308f58ee2"
down_revision = "d886acb494ca"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "update facility_scada set eoi_quantity = null where network_id='NEM'"
    )


def downgrade() -> None:
    pass
