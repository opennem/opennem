# pylint: disable=no-member
"""
Facility scada remove redundant interconnect data

Revision ID: 4569d3c0509e
Revises: 000e7fdab7e2
Create Date: 2020-12-24 15:09:21.715722

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "4569d3c0509e"
down_revision = "000e7fdab7e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "delete from facility_scada where facility_code in ('V-SA-3', 'V-SA-4', 'N-Q-MNSP1-3', 'N-Q-MNSP1-4', 'NSW1-QLD1-3', 'NSW1-QLD1-4', 'V-S-MNSP1-3', 'V-S-MNSP1-4', 'T-V-MNSP1-3', 'T-V-MNSP1-4', 'VIC1-NSW1-3', 'VIC1-NSW1-4')"
    )


def downgrade() -> None:
    pass
