select
  f.network_id,
  f.network_region,
  ftg.code as fueltech_id,
  ftg.label as fueltech_label,
  aggr.highest_output,
  aggr.lowest_output,
  max(fs.trading_interval) filter (where fs.generated = aggr.highest_output) as highest_output_interval,
  max(fs.trading_interval) filter (where fs.generated = aggr.lowest_output) as lowest_output_interval
from facility_scada fs
join facility f on fs.facility_code = f.code
join fueltech ft on f.fueltech_id = ft.code
join fueltech_group ftg on ftg.code = ft.fueltech_group_id
join (
  select
    f_inner.network_region,
    ft_inner.label as fueltech_label,
    max(fs_inner.generated) as highest_output,
    min(fs_inner.generated) as lowest_output
  from facility_scada fs_inner
  join facility f_inner on fs_inner.facility_code = f_inner.code
  join fueltech ft_inner on f_inner.fueltech_id = ft_inner.code
  where
    fs_inner.trading_interval >= now() at time zone 'aest' - interval '180 days' and
    fs_inner.generated >= 0
  group by f_inner.network_region, ft_inner.code
  ) as aggr on f.network_region = aggr.network_region and ft.label = aggr.fueltech_label
where
    fs.trading_interval >= now() at time zone 'aest' - interval '180 days' and
    f.network_id in ('aemo_rooftop', 'nem', 'wem')
group by f.network_id, f.network_region, ftg.code, ftg.label, aggr.highest_output, aggr.lowest_output;
