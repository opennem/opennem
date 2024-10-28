# pylint: disable=no-member
"""
Clean up locations

Revision ID: 2c915e2291c4
Revises: 1c1004a2c283
Create Date: 2021-07-27 06:22:35.597871

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "2c915e2291c4"
down_revision = "1c1004a2c283"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("delete from location where id not in (select location_id from station);")


def downgrade() -> None:
    pass
