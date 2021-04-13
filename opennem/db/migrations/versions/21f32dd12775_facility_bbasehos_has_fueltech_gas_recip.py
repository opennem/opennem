# pylint: disable=no-member
"""
Facility BBASEHOS has fueltech BBASEHOS

Revision ID: 21f32dd12775
Revises: 0995118b97ec
Create Date: 2021-04-14 00:27:38.951016

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "21f32dd12775"
down_revision = "0995118b97ec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("update facility set fueltech_id='gas_recip' where code = 'BBASEHOS';")


def downgrade() -> None:
    pass
