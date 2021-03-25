create materialized view mv_network_fueltech_days as
select
    date_trunc('day', fs.trading_interval at time zone 'AEST') as trading_day,
    f.code,
    f.fueltech_id,
    f.network_id,
    f.network_region,
    f.interconnector,
    f.interconnector_region_to,
    max(fs.energy) as energy,
    case when max(bs.price_dispatch) >= 0  and min(fs.energy) >= 0 then
        coalesce(
            sum(fs.energy) * max(bs.price_dispatch),
            0.0
        )
    else 0.0
    end as market_value,
    case when min(f.emissions_factor_co2) >= 0  and min(fs.energy) >= 0 then
        coalesce(
            sum(fs.energy) * min(f.emissions_factor_co2),
            0.0
        )
    else 0.0
    end as emissions
from (
  select
      time_bucket('30 minutes', fs.trading_interval) as trading_interval,
      fs.facility_code,
      fs.network_id,
      sum(fs.eoi_quantity) as energy
  from facility_scada fs
  where fs.is_forecast is False
  group by
      1, 2, 3
) as fs
    left join facility f on fs.facility_code = f.code
    left join balancing_summary bs on
        bs.trading_interval = fs.trading_interval
        and bs.network_id=f.network_id
        and bs.network_region = f.network_region
where
    f.fueltech_id is not null
group by
    1,
    f.code,
    f.fueltech_id,
    f.network_id,
    f.network_region,
    f.interconnector,
    f.interconnector_region_to
order by 1 desc;

create index idx_mv_network_fueltech_days_trading_day on mv_network_fueltech_days (trading_day desc);
create index idx_mv_network_fueltech_days_trading_day_code on mv_network_fueltech_days (trading_day desc, code);
create index idx_mv_network_fueltech_days_trading_day_fueltech_id on mv_network_fueltech_days (trading_day desc, fueltech_id);
create index idx_mv_network_fueltech_days_code on mv_network_fueltech_days (code);
create index idx_mv_network_fueltech_days_fueltech on mv_network_fueltech_days (fueltech_id);
create index idx_mv_network_fueltech_days_network_id on mv_network_fueltech_days (network_id);
create index idx_mv_network_fueltech_days_network_region on mv_network_fueltech_days (network_region);
