CREATE MATERIALIZED VIEW mv_facility_energy_hour WITH (timescaledb.continuous) AS
select
    time_bucket('1 hour', fs.trading_interval) as trading_interval,
    fs.facility_code,
    fs.network_id,
    (case
        when count(fs.eoi_quantity) > 0 then sum(fs.eoi_quantity)
        else energy_sum(fs.generated, '1 hour') * interval_size('1 hour', count(fs.generated))
    end) as energy
from facility_scada fs
where fs.is_forecast is False
group by
    1, 2, 3;
