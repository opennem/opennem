create materialized view mv_facility_all as
select
    fs.trading_interval,
    f.code,
    f.fueltech_id,
    f.network_id,
    f.network_region,
    f.interconnector,
    f.interconnector_region_to,
    date_trunc('day', fs.trading_interval at time zone 'AEST') as ti_day_aest,
    date_trunc('month', fs.trading_interval at time zone 'AEST') as ti_month_aest,
    date_trunc('day', fs.trading_interval at time zone 'AWST') as ti_day_awst,
    date_trunc('month', fs.trading_interval at time zone 'AWST') as ti_month_awst,
    round(max(fs.energy), 4) as energy,
    case when max(bs.price_dispatch) >= 0  and min(fs.energy) >= 0 then
        coalesce(
            round(max(fs.energy) * max(bs.price_dispatch), 4),
            0.0
        )
    else 0.0
    end as market_value,
    case when min(f.emissions_factor_co2) >= 0  and min(fs.energy) >= 0 then
        coalesce(
            round(max(fs.energy) * min(f.emissions_factor_co2), 4),
            0.0
        )
    else 0.0
    end as emissions
from (
  select
      time_bucket('30 minutes', fs.trading_interval) as trading_interval,
      fs.facility_code,
      fs.network_id,
      round(sum(fs.eoi_quantity), 4) as energy
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
group by
    1,
    f.code,
    f.fueltech_id,
    f.network_id,
    f.network_region,
    f.interconnector,
    f.interconnector_region_to
order by 1 desc;

create unique index if not exists idx_mv_facility_all_unique on mv_facility_all (trading_interval, network_id, code);

-- field indexes
create index if not exists idx_mv_facility_all_trading_interval on mv_facility_all (trading_interval);
create index if not exists idx_mv_facility_all_code on mv_facility_all (code);
create index if not exists idx_mv_facility_all_network_id on mv_facility_all (network_id);
create index if not exists idx_mv_facility_all_network_region on mv_facility_all (network_region);
create index if not exists idx_mv_facility_all_interconnector on mv_facility_all (interconnector);

-- date indexes
create index if not exists idx_trading_interval_code_index on mv_facility_all (trading_interval desc, code);
create index if not exists idx_trading_day_aest_index on mv_facility_all (ti_day_aest desc);
create index if not exists idx_trading_day_aest_code_index on mv_facility_all (ti_day_aest desc, code);
create index if not exists idx_trading_month_aest_code_index on mv_facility_all (ti_month_aest desc, code);
create index if not exists idx_trading_day_awst_index on mv_facility_all (ti_day_awst desc);
create index if not exists idx_trading_day_awst_code_index on mv_facility_all (ti_day_awst desc, code);
create index if not exists idx_trading_month_awst_code_index on mv_facility_all (ti_month_awst desc, code);


-- other indexes
create index if not exists idx_trading_interval_code_index on mv_facility_all (trading_interval desc, code);
create index if not exists idx_trading_day_aest_code_index on mv_facility_all (ti_day_aest desc, code);
create index if not exists idx_trading_month_aest_code_index on mv_facility_all (ti_month_aest desc, code);
create index if not exists idx_trading_day_awst_code_index on mv_facility_all (ti_day_awst desc, code);
create index if not exists idx_trading_month_awst_code_index on mv_facility_all (ti_month_awst desc, code);
