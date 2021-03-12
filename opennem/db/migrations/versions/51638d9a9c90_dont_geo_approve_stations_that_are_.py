# pylint: disable=no-member
"""
Dont geo approve stations that are rooftop, interconnectors or flows

Revision ID: 51638d9a9c90
Revises: 4c45ec418fea
Create Date: 2021-03-12 13:48:51.879371

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "51638d9a9c90"
down_revision = "4c45ec418fea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "update station set approved=FALSE where code LIKE 'NEM_FLOW_%' or code LIKE 'ROOFTOP_%' or code in ('V-SA', 'N-Q-MNSP1', 'NSW1-QLD1', 'V-S-MNSP1', 'T-V-MNSP1', 'VIC1-NSW1')"
    )


def downgrade() -> None:
    pass
