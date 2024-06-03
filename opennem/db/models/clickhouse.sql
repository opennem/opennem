create database if not exists opennem;
create database if not exists apilogs;

drop dictionary if exists facilities;
-- drop table if exists facility_scada;
drop table if exists agg_power_per_interval_region_fueltech;
drop view if exists agg_power_per_interval_region_fueltech_mv;

create dictionary if not exists opennem.facilities (
	code String,
    network_id String default 'NEM',
    network_region String,
    dispatch_type String,
    fueltech_id String,
    status_id String,
    emission_factor_co2 Float32 default 0,
    interconnector Bool default false,
    interconnector_region_from Nullable(String),
    interconnector_region_to Nullable(String)
)
primary key code, network_id, network_region
source(
	postgresql(
		port 5432
		host 'db01'
		user 'opennem-re'
		password 'rmmPpAaHtktbOjXf9AhvAFx0mremAKUz7eKw+eQdtcQ'
		db 'opennem'
		query 'select
            code,
            network_id,
            network_region,
            dispatch_type,
            fueltech_id,
            status_id,
            emissions_factor_co2,
            interconnector,
            interconnector_region_from,
            interconnector_region_to
        from facility
        where
            fueltech_id is not null'
	)
)
LIFETIME(MIN 0 MAX 360)
LAYOUT(HASHED_ARRAY());

-- scada table
CREATE TABLE if not exists opennem.facility_scada (
    trading_interval DateTime(),
    facility_code String,
    generated Float64 default 0,
    is_forecast bool default false
)
ENGINE = MergeTree
primary key (trading_interval, facility_code);

-- balancing summary table
CREATE TABLE IF NOT EXISTS opennem.balancing_summary (
    trading_interval DateTime(),
    network_id String,
    network_region String,
    price Float64 default 0,
    demand Float64 default 0,
    generation Float64 default 0,
    is_forecast bool default false
)
ENGINE = MergeTree
primary key (trading_interval, network_id, network_region)
ORDER BY (trading_interval, network_id, network_region);

--
-- Materialized Views
--

CREATE TABLE IF NOT EXISTS opennem.agg_power_per_interval_region_fueltech (
    trading_interval DateTime(),
    network_id String,
    network_region String,
    fueltech_id String,
    generated Float64 default 0,
    emissions Float64 default 0,
)
ENGINE = MergeTree
primary key (trading_interval, network_id, network_region, fueltech_id)
ORDER BY (trading_interval, network_id, network_region, fueltech_id);

CREATE MATERIALIZED VIEW IF NOT EXISTS opennem.agg_power_per_interval_region_fueltech_mv
TO opennem.agg_power_per_interval_region_fueltech AS
SELECT
    fs.trading_interval,
    f.network_id,
    f.network_region,
    f.fueltech_id,
    greatest(SUM(fs.generated), 0) AS generated,
    greatest(SUM(fs.generated) * max(f.emission_factor_co2) / 12, 0) AS emissions
FROM opennem.facility_scada AS fs
JOIN opennem.facilities AS f ON fs.facility_code = f.code
WHERE
    f.fueltech_id IS NOT NULL AND
    f.fueltech_id NOT IN ('imports', 'exports', 'interconnector')
    AND fs.is_forecast = FALSE
    AND fs.trading_interval >= toTimeZone(now(), 'Australia/Brisbane') - INTERVAL 45 DAY
GROUP BY
    1, 2, 3, 4
ORDER BY 1 DESC, 2, 3, 4;

INSERT INTO opennem.agg_power_per_interval_region_fueltech_mv
SELECT
    fs.trading_interval,
    f.network_id,
    f.network_region,
    f.fueltech_id,
    greatest(SUM(fs.generated), 0) AS generated,
    greatest(SUM(fs.generated) * max(f.emission_factor_co2) / 12, 0) AS emissions
FROM opennem.facility_scada AS fs
JOIN opennem.facilities AS f ON fs.facility_code = f.code
WHERE
    f.fueltech_id IS NOT NULL AND
    f.fueltech_id NOT IN ('imports', 'exports', 'interconnector')
    AND fs.is_forecast = FALSE
    AND fs.trading_interval >= toTimeZone(now(), 'Australia/Brisbane') - INTERVAL 45 DAY
GROUP BY
    1, 2, 3, 4
ORDER BY 1 DESC, 2, 3, 4;
