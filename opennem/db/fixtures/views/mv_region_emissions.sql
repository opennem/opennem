create materialized view mv_region_emissions as select
    f.trading_interval,
    f.network_id,
    f.network_region,
    case
        when sum(f.energy) > 0 then
            sum(f.emissions) / sum(f.energy)
        else 0
    end as emissions_per_mw
from mv_facility_all f
group by 1, 2, f.network_region
order by 1 desc;
