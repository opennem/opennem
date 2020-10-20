"""Update energy sum functions

Revision ID: 4ee58f229572
Revises: 7c5a5ddfb9e1
Create Date: 2020-10-20 19:51:14.874586

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "4ee58f229572"
down_revision = "7c5a5ddfb9e1"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        drop function if exists agg_power(agg_state point, el numeric, interval_size_minutes int) cascade;
        drop function if exists agg_power(agg_state numeric[], el numeric, text) cascade;
        drop function if exists agg_power(agg_state numeric[], el numeric) cascade;

        create function agg_power(agg_state numeric[], el numeric)
        returns numeric[]
        immutable
        language plpgsql
        as $$
        begin
            agg_state := agg_state || el;
            return agg_state;
        end;
        $$;
    """
    )

    op.execute(
        """

        drop function if exists onenergy_finalfunc(agg_state point) cascade;

        drop function if exists onenergy_finalfunc(agg_state numeric[]);

        create function onenergy_finalfunc(agg_state numeric[])
        returns float8
        immutable
        strict
        language plpgsql
        as $$
        declare
            result_int numeric;
            divis numeric;
            bucket_size_minutes int := 0;
            m numeric;
            cur_index int := 1;
            current_sum numeric := 0;
            power_interval numeric;
            num_intervals int;
            a float := 0;
            b float := 1;
            n float := 10;
            w int := 0;
            h float := (b - a) / n;
        begin
            bucket_size_minutes := extract(epoch FROM '1 day'::interval) / 60;

            num_intervals := array_length(agg_state, 1);

            FOREACH m IN ARRAY agg_state
            LOOP
                IF cur_index = 1 then
                    w := 1;
                elsif cur_index = (n + 1) then
                    w := 1;
                elsif (cur_index % 2) = 1 then
                    w := 2;
                else
                    w := 4;
                END IF;

                cur_index := cur_index + 1;

                divis := (60 / (bucket_size_minutes / num_intervals));

                if m > 0 and divis > 0 then
                    power_interval = m / divis;
                else
                    power_interval = 0;
                end if;

                current_sum = current_sum + (w * power_interval);
            END LOOP;

            result_int := h * current_sum / 6 * 10;

            return round(result_int, 2);
        end;
        $$;
    """
    )

    op.execute(
        """
        create aggregate on_energy_sum (numeric)
        (
            sfunc = agg_power,
            stype = numeric[],
            finalfunc = onenergy_finalfunc,
            initcond = '{}'
        );
    """
    )


def downgrade():
    op.execute(
        "drop aggregate if exists on_energy_sum (numeric, text) cascade"
    )
    op.execute(
        "drop function if exists agg_power (agg_state numeric[], el numeric) cascade"
    )
    op.execute(
        "drop function if exists onenergy_finalfunc (agg_state numeric[]) cascade"
    )
