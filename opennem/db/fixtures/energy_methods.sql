drop aggregate if exists on_energy_sum (numeric, text) cascade;

drop type if exists tenergy cascade;
CREATE TYPE tenergy AS (
    items       numeric[],
    bucket_size_minutes    int
);

drop function if exists agg_power(tenergy, numeric, text);

create function agg_power(agg_state tenergy, el numeric, bucket_interval text)
returns tenergy
immutable
language plpgsql
as $$
begin
	agg_state.bucket_size_minutes := extract(epoch FROM bucket_interval::interval) / 60;
	agg_state.items := agg_state.items || el;

	return agg_state;
end;
$$;

drop function if exists onenergy_finalfunc (agg_state tenergy) cascade;

create function onenergy_finalfunc(agg_state tenergy)
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

create aggregate on_energy_sum (numeric, bucket_size text)
(
    sfunc = agg_power,
    stype = tenergy,
    finalfunc = onenergy_finalfunc,
    initcond = '({}, 0)'
);
