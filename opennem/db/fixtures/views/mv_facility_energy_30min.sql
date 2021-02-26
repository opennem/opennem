CREATE MATERIALIZED VIEW mv_facility_energy_30m WITH (timescaledb.continuous) AS
select
    time_bucket('30 minutes', fs.trading_interval) as trading_interval,
    fs.facility_code,
    fs.network_id,
    round(sum(fs.eoi_quantity), 4) as energy
from facility_scada fs
where fs.is_forecast is False
group by
    1, 2, 3;
