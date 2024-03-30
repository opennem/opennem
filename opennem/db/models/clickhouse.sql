-- drop dictionary if exists facilities;
drop table if exists facility_scada;

create dictionary if not exists facilities (
	code String,
    network_id String default 'NEM',
    network_region String,
    dispatch_type String,
    fueltech_id String,
    status_id String,
    emission_factor_co2 Float32 default 0,
    interconnector Bool,
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
        from facility'
	)
)
LIFETIME(MIN 0 MAX 360)
LAYOUT(HASHED_ARRAY());

CREATE TABLE if not exists facility_scada (
    trading_interval DateTime(),
    facility_code String,
    generated Float64 default 0,
    is_forecast bool default false
)
ENGINE = MergeTree
primary key (trading_interval, facility_code);
