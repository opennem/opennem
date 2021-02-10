create materialized view mv_interchange_energy_nem_region AS
select
    time_bucket('1 hour', e.trading_interval) as trading_interval,
    e.network_id,
    e.network_region,
    sum(e.import_energy) / 1000 as imports_energy,
    sum(e.export_energy) / 1000 as exports_energy
from (
    select
        time_bucket('30 minutes', t.trading_interval) as trading_interval,
        t.network_id,
        t.network_region,
        0.5 * avg(t.imports) as import_energy,
        0.5 * avg(t.exports) as export_energy
    from (select
            bs.trading_interval at time zone 'AEST' as trading_interval,
            bs.network_id,
            bs.network_region,
            case when bs.net_interchange < 0 then bs.net_interchange else 0 end as imports,
            case when bs.net_interchange > 0 then bs.net_interchange else 0 end as exports
        from balancing_summary bs
        where
            bs.net_interchange is not null
    ) as t
    group by 1, 2, 3
) as e
group by 1, 2, 3
order by 1 asc;
