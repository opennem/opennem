# pylint: disable=no-member
"""Update on_energy_sum to support variable interval sizes, custom
tenergy type, and calculate using built-in polygon functions

Revision ID: 4fb955a7a2a7
Revises: bb6fb4645ca3
Create Date: 2020-10-21 17:35:48.326616

"""
from alembic import op

from opennem.core.loader import load_data

# revision identifiers, used by Alembic.
revision = "4fb955a7a2a7"
down_revision = "bb6fb4645ca3"
branch_labels = None
depends_on = None


def upgrade():
    # ENERGY_FUNCTIONS = load_data("energy_methods.sql", from_fixture=True)

    op.execute(
        """drop type if exists tenergy cascade;
CREATE TYPE tenergy AS (
    items       numeric[],
    bucket_size_minutes    int
);"""
    )

    op.execute(
        "drop aggregate if exists on_energy_sum (numeric, text) cascade"
    )
    op.execute(
        """drop function if exists agg_power(agg_state numeric[], el numeric)
        cascade"""
    )
    op.execute(
        "drop function if exists onenergy_finalfunc(agg_state numeric[])"
    )

    # op.execute(ENERGY_FUNCTIONS)


def downgrade():
    op.execute(
        "drop aggregate if exists on_energy_sum (numeric, text) cascade"
    )
    op.execute("drop type if exists tenergy cascade")
