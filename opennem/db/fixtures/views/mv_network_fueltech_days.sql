create materialized view mv_network_fueltech_days as
  select
    date_trunc('day', f.trading_interval at time zone n.timezone_database) as trading_day,
    f.code,
    f.fueltech_id,
    f.network_id,
    f.network_region,
    f.interconnector,
    f.interconnector_region_to,
    sum(f.energy) as energy,
    sum(f.market_value) as market_value,
    sum(f.emissions) as emissions
  from (
    select
        time_bucket('30 minutes', fs.trading_interval) as trading_interval,
        fs.facility_code as code,
        f.fueltech_id,
        fs.network_id,
        f.network_region,
        f.interconnector,
        f.interconnector_region_to,
        sum(fs.eoi_quantity) as energy,
        sum(fs.eoi_quantity) * max(bs.price) as market_value,
        sum(fs.eoi_quantity) * max(f.emissions_factor_co2) as emissions
    from facility_scada fs
      left join facility f on fs.facility_code = f.code
      left join network n on f.network_id = n.code
      left join balancing_summary bs on
          bs.trading_interval - INTERVAL '1 minute' * n.interval_shift = fs.trading_interval
          and bs.network_id = n.network_price
          and bs.network_region = f.network_region
    where fs.is_forecast is False
    group by
        1, 2, 3, 4, 5, 6, 7
order by 1 desc;

create unique index idx_mv_network_fueltech_days_unique_trading_day_network_id_code on mv_network_fueltech_days (trading_day, network_id, code);
create index idx_mv_network_fueltech_days_trading_day on mv_network_fueltech_days (trading_day desc);
create index idx_mv_network_fueltech_days_trading_day_code on mv_network_fueltech_days (trading_day desc, code);
create index idx_mv_network_fueltech_days_trading_day_fueltech_id on mv_network_fueltech_days (trading_day desc, fueltech_id);
create index idx_mv_network_fueltech_days_code on mv_network_fueltech_days (code);
create index idx_mv_network_fueltech_days_fueltech on mv_network_fueltech_days (fueltech_id);
create index idx_mv_network_fueltech_days_network_id on mv_network_fueltech_days (network_id);
create index idx_mv_network_fueltech_days_network_region on mv_network_fueltech_days (network_region);
