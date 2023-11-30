select
  ftg.label as fueltech_group,
  f.network_region,
  aggr.highest_output,
  aggr.lowest_output,
  max(fd.trading_day) filter (where fd.energy = aggr.highest_output) as day_of_highest_output,
  min(fd.trading_day) filter (where fd.energy = aggr.lowest_output) as day_of_lowest_output
from at_facility_daily fd
join facility f on fd.facility_code = f.code
join fueltech ft on f.fueltech_id = ft.code
join fueltech_group ftg on ft.fueltech_group_id = ftg.code
join (
  select
    ftg_inner.label as fueltech_group_label,
    f_inner.network_region as network_region_label,
    max(fd_inner.energy) as highest_output,
    min(fd_inner.energy) as lowest_output
  from at_facility_daily fd_inner
  join facility f_inner on fd_inner.facility_code = f_inner.code
  join fueltech ft_inner on f_inner.fueltech_id = ft_inner.code
  join fueltech_group ftg_inner on ft_inner.fueltech_group_id = ftg_inner.code
  where fd_inner.trading_day >= current_date - interval '90 days'
  group by ftg_inner.label, f_inner.network_region
) as aggr on ftg.label = aggr.fueltech_group_label and f.network_region = aggr.network_region_label
where fd.trading_day >= current_date - interval '90 days'
group by ftg.label, f.network_region, aggr.highest_output, aggr.lowest_output
order by ftg.label, f.network_region;
