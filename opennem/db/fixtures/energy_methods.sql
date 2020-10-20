-- OpenNEM energy aggregate functions
--
-- Postgres functions and aggregate for calculate energy
-- any feedback improvements please contribute


-- Example query used with timescaledb buckets:
--
-- @NOTE https://gist.github.com/nc9/9679b9f025bb360910bb3cc49173818d


drop aggregate if exists energy_total (numeric, int);
drop function if exists agg_power (agg_state point, el numeric, interval_size_minutes int);
drop function if exists onenergy_finalfunc;

drop aggregate if exists on_energy_sum (numeric, text);
drop function if exists agg_power (agg_state numeric[], el numeric, text);
drop function if exists onenergy_finalfunc (agg_state numeric[]);

create function agg_power(agg_state numeric[], el numeric, text)
returns numeric[]
immutable
language plpgsql
as $$
begin

	agg_state := agg_state || el;

	return agg_state;
end;
$$;

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

create aggregate on_energy_sum (numeric)
(
    sfunc = agg_power,
    stype = numeric[],
    finalfunc = onenergy_finalfunc,
    initcond = '{}'
);
