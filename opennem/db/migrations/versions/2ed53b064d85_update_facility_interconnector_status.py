# pylint: disable=no-member
"""
Update facility interconnector status

Revision ID: 2ed53b064d85
Revises: ddb5d2a90896
Create Date: 2021-02-16 23:58:10.961598

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2ed53b064d85"
down_revision = "ddb5d2a90896"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update facility set interconnector=False where interconnector is null")


def downgrade() -> None:
    pass
