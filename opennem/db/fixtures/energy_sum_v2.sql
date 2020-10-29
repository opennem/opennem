--drop aggregate if exists on_energy_sum (numeric, text) cascade;
--drop function if exists agg_power(tenergy, numeric, text);
--drop function if exists onenergy_finalfunc (agg_state tenergy) cascade;
--
--
--drop type if exists tenergy cascade;
--

drop aggregate if exists energy_sum(numeric, text) cascade;

drop type if exists agg_state_energy cascade;

CREATE TYPE agg_state_energy AS (
    count       int,
    last_x 		numeric,
    energy_sum 	numeric,
    is_first 	boolean
);

create function sum_area(agg_state agg_state_energy, el numeric, bucket_interval text)
returns agg_state_energy
immutable
language plpgsql
as $$
declare
	trap_val numeric;

begin
    agg_state.count = agg_state.count + 1;

    if agg_state.is_first then
    	agg_state.is_first = FALSE;
    	agg_state.last_x = el;
    	return agg_state;
    end if;

    trap_val := agg_state.last_x + ((el - agg_state.last_x) / 2);

    agg_state.energy_sum := agg_state.energy_sum + trap_val;
    agg_state.last_x = el;

    return agg_state;
end;
$$;


drop function if exists energy_sum_pop(agg_state_energy);
create function energy_sum_pop(agg_state agg_state_energy)
returns numeric
immutable
language plpgsql
as $$
begin
    return agg_state.energy_sum / 60;

end;
$$;



create aggregate energy_sum (numeric, bucket_size text)
(
	sfunc = sum_area,
	stype = agg_state_energy,
	finalfunc = energy_sum_pop,
	initcond = '(0,,0.0, TRUE)'
);

drop function if exists interval_size(text, numeric);
create function interval_size(bucket_interval text, sample_count numeric)
returns numeric
immutable
language plpgsql
as $$
begin
	return extract(epoch FROM bucket_interval::interval) / 60 / sample_count;
end;
$$;
