# pylint: disable=no-member
"""
Make energy_sum as parallel safe

Revision ID: d8bd4db7c53d
Revises: e79ef4fd3653
Create Date: 2020-12-11 17:13:27.201643

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d8bd4db7c53d"
down_revision = "e79ef4fd3653"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        create or replace function energy_sum_combine_states(agg_state agg_state_energy, agg_state2 agg_state_energy)
        returns agg_state_energy
        immutable
        language plpgsql
        as $$
        declare
            agg_state_return agg_state_energy;

        begin
            agg_state_return = agg_state;
            agg_state_return.energy_sum = agg_state_return.energy_sum + agg_state2.energy_sum;

            return agg_state_return;
        end;
        $$;

        create or replace aggregate energy_sum (numeric, bucket_size text)
        (
            sfunc = sum_area,
            stype = agg_state_energy,
            finalfunc = energy_sum_pop,
            initcond = '(0,,0.0, TRUE)',
            COMBINEFUNC = energy_sum_combine_states,
            PARALLEL = SAFE
        );
        """
    )


def downgrade() -> None:
    pass
