with
generation as (
    select
        fd.trading_day::date,
        'NEM' as network_id,
        f.network_region,
        round(sum(fd.energy), 2) as energy_total
    from at_facility_daily fd
    left join facility f on f.code = fd.facility_code
    left join fueltech ft on f.fueltech_id = ft.code
    where
        f.dispatch_type = 'GENERATOR' and
        fd.network_id in ('NEM', 'AEMO_ROOFTOP') and
        f.fueltech_id not in ('imports', 'exports', 'interconnector', 'battery_charging') and
        fd.energy > 0
    group by 1, 2, 3
),

generation_by_fueltech as (
    select
        fd.trading_day::date,
        'NEM' as network_id,
        f.network_region,
        ft.code as fueltech_id,
        round(sum(fd.energy), 2) as energy_total
    from at_facility_daily fd
    left join facility f on f.code = fd.facility_code
    left join fueltech ft on f.fueltech_id = ft.code
    where
        f.dispatch_type = 'GENERATOR' and
        fd.network_id in ('NEM', 'AEMO_ROOFTOP') and
        f.fueltech_id not in ('imports', 'exports', 'interconnector', 'battery_charging') and
        fd.energy > 0
    group by 1, 2, 3, 4
),

generation_renewable as (
    select
        fd.trading_day::date,
        'NEM' as network_id,
        f.network_region,
        round(sum(fd.energy), 2) as energy_total
    from at_facility_daily fd
    left join facility f on f.code = fd.facility_code
    left join fueltech ft on f.fueltech_id = ft.code
    where
        f.dispatch_type = 'GENERATOR' and
        fd.network_id in ('NEM', 'AEMO_ROOFTOP') and
        f.fueltech_id not in ('imports', 'exports', 'interconnector', 'battery_charging') and
        ft.renewable is True and
        fd.energy > 0
    group by 1, 2, 3
),

flows_region_daily as (
    select
        date_trunc('day', fl.trading_interval at time zone 'AEST')::date as trading_day,
        fl.network_id,
        fl.network_region,
        round(sum(fl.energy_imports) * -1 , 2) as energy_imports,
        round(sum(fl.energy_exports), 2) as energy_exports
    from at_network_flows fl
    group by 1, 2, 3
),

pumps as (
    select
        fd.trading_day::date,
        fd.network_id,
        f.network_region,
        round(sum(fd.energy), 2) as energy_total
    from at_facility_daily fd
    left join facility f on f.code = fd.facility_code
    left join fueltech ft on f.fueltech_id = ft.code
    where
        fd.network_id in ('NEM') and
        f.fueltech_id in ('pumps')
    group by 1, 2, 3
),

battery_charging as (
    select
        fd.trading_day::date,
        fd.network_id,
        f.network_region,
        round(sum(fd.energy), 2) as energy_total
    from at_facility_daily fd
    left join facility f on f.code = fd.facility_code
    left join fueltech ft on f.fueltech_id = ft.code
    where
        fd.network_id in ('NEM') and
        f.fueltech_id in ('battery_charging')
    group by 1, 2, 3
 )
