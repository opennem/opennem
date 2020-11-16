# pylint: disable=no-member
"""FIX: cast m nulls to 0 in om_energy_sum

Revision ID: f87394cc4c00
Revises: 4fb955a7a2a7
Create Date: 2020-10-21 18:44:31.318648

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "f87394cc4c00"
down_revision = "4fb955a7a2a7"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
    create or replace function onenergy_finalfunc(agg_state tenergy)
    returns numeric
    immutable
    language plpgsql
    as $$
    declare
        result_int numeric;
        num_intervals int;
        poly text = '';
        poly_array text[] = '{}';
        interval_size_minutes int;
        y int := 0;
        m int;
    begin
        num_intervals := array_length(agg_state.items, 1);
        interval_size_minutes := agg_state.bucket_size_minutes / num_intervals;

        poly_array = poly_array || format('%s %s', 0, 0);

        FOREACH m IN ARRAY agg_state.items
        LOOP
            m := coalesce(m, 0);

            poly_array = poly_array || format('%s %s', y, m);
            y := y + interval_size_minutes;

        END LOOP;

        poly_array = poly_array || format('%s %s', agg_state.bucket_size_minutes, 0);
        poly_array = poly_array || format('%s %s', 0, 0);


        poly := format('POLYGON((%s))', array_to_string(poly_array, ', '));

        result_int := (ST_AREA(poly::geometry) / 60)::numeric;

        return result_int;
    end;
    $$;
    """
    )


def downgrade():
    pass
