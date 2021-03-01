create materialized view mv_interchange_energy_nem_region AS
select
    time_bucket('1 hour', e.trading_interval) as trading_interval,
    e.network_id,
    e.network_region,
    sum(e.import_energy) / 1000 as imports_energy,
    sum(e.export_energy) / 1000 as exports_energy,

    -- import
    case when max(e.price_dispatch) >= 0  and min(abs(e.import_energy)) >= 0 then
        coalesce(
            round(abs(sum(e.import_energy)) * max(e.price_dispatch), 4),
            0.0
        )
    else NULL
    end as imports_market_value,

    -- export
    case when max(e.price_dispatch) >= 0  and min(e.export_energy) >= 0 then
        coalesce(
            round(abs(sum(e.export_energy)) * max(e.price_dispatch), 4),
            0.0
        )
    else NULL
    end as exports_market_value,

    -- import price
    case when max(e.price_dispatch) >= 0  and min(abs(e.import_energy)) >= 0 then
        coalesce(
            round(abs(sum(e.import_energy)) * max(e.price), 4),
            0.0
        )
    else NULL
    end as imports_market_value_rrp,

    -- export price
    case when max(e.price_dispatch) >= 0  and min(e.export_energy) >= 0 then
        coalesce(
            round(abs(sum(e.export_energy)) * max(e.price), 4),
            0.0
        )
    else NULL
    end as exports_market_value_rrp
from (
    select
        time_bucket('30 minutes', t.trading_interval) as trading_interval,
        t.network_id,
        t.network_region,
        0.5 * avg(t.imports) as import_energy,
        0.5 * avg(t.exports) as export_energy,
        avg(t.price) as price,
        avg(t.price_dispatch) as price_dispatch
    from (select
            bs.trading_interval at time zone 'AEST' as trading_interval,
            bs.network_id,
            bs.network_region,
            case when bs.net_interchange < 0 then bs.net_interchange else 0 end as imports,
            case when bs.net_interchange > 0 then bs.net_interchange else 0 end as exports,
            bs.price,
            bs.price_dispatch
        from balancing_summary bs
        where
            bs.net_interchange is not null
    ) as t
    group by 1, 2, 3
) as e
group by 1, 2, 3
order by 1 asc;
