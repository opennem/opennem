create materialized view mv_region_emissions_45d as select
    f.trading_interval,
    f.network_id,
    f.network_region,
    case
        when sum(f.energy) > 0 then
            sum(f.emissions) / sum(f.energy) * 0.5
        else 0
    end as emissions_per_mw
from mv_facility_45d f
group by 1, 2, f.network_region
order by 1 desc;


create unique index if not exists idx_mv_region_emissions_45d_unique on mv_region_emissions_45d (trading_interval, network_id, network_region);

create index if not exists idx_mv_region_emissions_45d_trading_interval on mv_region_emissions_45d (trading_interval desc);
create index if not exists idx_mv_region_emissions_45d_network_id on mv_region_emissions_45d (network_id);
