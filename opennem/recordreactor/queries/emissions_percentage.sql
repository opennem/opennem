select
    generation.trading_day,
    generation.network_id,
    generation.network_region,
    round(sum(generation.energy_total), 2) as generation_total,
    round(sum(generation_renewable.energy_total), 2) as generation_renewable,
    round(sum(pumps.energy_total), 2) as pumps_total,
    round(sum(battery_charging.energy_total), 2) as battery_discharging_total,
    round(sum(flows_region_daily.energy_imports), 2) as energy_imports,
    round(sum(flows_region_daily.energy_exports), 2) as energy_exports,
    round(
                (sum(generation.energy_total)
                + sum(flows_region_daily.energy_imports)
                - sum(flows_region_daily.energy_exports)
                - sum(battery_charging.energy_total))

             , 2) as net_demand,
    round(sum(nd.demand_energy * 1000), 2) as at_demand,
    round(
        (
            sum(generation_renewable.energy_total) /
            (
                sum(generation.energy_total)
                + sum(flows_region_daily.energy_imports)
                - sum(flows_region_daily.energy_exports)
                - sum(battery_charging.energy_total)
             )

        ) * 100
    , 2) as generation_proportion,
    round(
        (sum(generation_renewable.energy_total) / sum(nd.demand_energy * 1000)) * 100
    , 2) as demand_proportion
from generation
inner join generation_renewable on
    generation.trading_day = generation_renewable.trading_day and
    generation.network_id = generation_renewable.network_id and
    generation.network_region = generation_renewable.network_region
join at_network_demand nd on
    generation.trading_day = nd.trading_day and
    generation.network_id = nd.network_id and
    generation.network_region = nd.network_region
inner join flows_region_daily on
    generation.trading_day = flows_region_daily.trading_day and
    generation.network_id = flows_region_daily.network_id and
    generation.network_region = flows_region_daily.network_region
inner join pumps on
    generation.trading_day = pumps.trading_day and
    generation.network_id = pumps.network_id and
    generation.network_region = pumps.network_region
inner join battery_charging on
    generation.trading_day = battery_charging.trading_day and
    generation.network_id = battery_charging.network_id and
    generation.network_region = battery_charging.network_region
where
    generation.network_id = 'NEM' and
    -- generation.network_region='NSW1' and
    generation.trading_day >= '2023-10-01' and
    generation.trading_day < now()::date and
    1=1
group by 1, 2, 3
order by 1 asc;
