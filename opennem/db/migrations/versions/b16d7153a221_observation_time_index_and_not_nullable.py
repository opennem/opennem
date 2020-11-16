# pylint: disable=no-member
"""observation_time index and not nullable

Revision ID: b16d7153a221
Revises: 637faac3f9c1
Create Date: 2020-10-22 00:54:37.709402

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "b16d7153a221"
down_revision = "637faac3f9c1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        op.f("ix_bom_observation_observation_time"),
        "bom_observation",
        ["observation_time"],
        unique=False,
    )
    op.drop_index(
        "bom_observation_observation_time_idx", table_name="bom_observation"
    )


def downgrade():
    op.create_index(
        "bom_observation_observation_time_idx",
        "bom_observation",
        ["observation_time"],
        unique=False,
    )
    op.drop_index(
        op.f("ix_bom_observation_observation_time"),
        table_name="bom_observation",
    )
