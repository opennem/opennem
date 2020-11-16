# pylint: disable=no-member,E501
"""observation_time timezone

Revision ID: 637faac3f9c1
Revises: f87394cc4c00
Create Date: 2020-10-22 00:43:25.578149

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "637faac3f9c1"
down_revision = "f87394cc4c00"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE bom_observation ALTER COLUMN observation_time TYPE TIMESTAMP WITH TIME ZONE USING observation_time AT TIME ZONE 'UTC'"
    )


def downgrade():
    op.execute(
        "ALTER TABLE bom_observation ALTER COLUMN observation_time TYPE TIMESTAMP WITHOUT TIME ZONE"
    )
