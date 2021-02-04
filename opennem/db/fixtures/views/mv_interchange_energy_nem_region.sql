CREATE MATERIALIZED VIEW mv_interchange_energy_nem_region WITH (timescaledb.continuous) AS
  select
      time_bucket('1 hour', bs.trading_interval) as trading_interval,
      bs.network_id,
      bs.network_region,
      case when sum(bs.net_interchange) < 0 then
          sum(bs.net_interchange) / 12
      else 0
      end as imports_avg,
      case when sum(bs.net_interchange) > 0 then
          sum(bs.net_interchange) / 12
      else 0
      end as exports_avg,
      --    energy sums
      case when sum(bs.net_interchange) < 0 then
          energy_sum(bs.net_interchange, '1 hour') * interval_size('1 hour', count(bs.net_interchange))
      else 0
      end as imports_energy,
      case when sum(bs.net_interchange) > 0 then
          energy_sum(bs.net_interchange, '1 hour') * interval_size('1 hour', count(bs.net_interchange))
      else 0
      end as exports_energy
  from balancing_summary bs
  group by 1, 2, 3;
