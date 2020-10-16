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

create function agg_power(agg_state point, el numeric, interval_size_minutes int)
returns point
immutable
language plpgsql
as $$
declare
  current_sum numeric := 0.0;
  num_elements int := 0;
  power_hour float := 0;
  n float := 10;
  w int := 0;
begin
 	num_elements = agg_state[1] + 1;

 	IF num_elements = 1 then
		w := 1;
	elsif num_elements = (n + 1) then
		w := 1;
	elsif (num_elements % 2) = 1 then
		w := 2;
	else
		w := 4;
	END IF;

	power_hour := el / (60 / interval_size_minutes);
 	current_sum := agg_state[0] + (w * power_hour);

 	return point(current_sum, num_elements);
end;
$$;

create function onenergy_finalfunc(agg_state point)
returns float8
immutable
strict
language plpgsql
as $$
declare
  result_int numeric = 0.0;
  a float := 0;
  b float := 1;
  n float := 10;
  h float := (b - a) / n;
begin
	result_int := h * agg_state[0] / 3 * 10;

  	return round(result_int, 2);
end;
$$;

create aggregate on_energy_sum (numeric, int)
(
    sfunc = agg_power,
    stype = point,
    finalfunc = onenergy_finalfunc,
    initcond = '(0,0)'
);
