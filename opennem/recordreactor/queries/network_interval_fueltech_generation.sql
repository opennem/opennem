SELECT
  f.network_id,
  f.network_region,
  ftg.code as fueltech_id,
  ftg.label AS fueltech_label,
  aggr.highest_output,
  aggr.lowest_output,
  MAX(fs.trading_interval) FILTER (WHERE fs.generated = aggr.highest_output) AS highest_output_interval,
  MAX(fs.trading_interval) FILTER (WHERE fs.generated = aggr.lowest_output) AS lowest_output_interval
FROM facility_scada fs
JOIN facility f ON fs.facility_code = f.code
JOIN fueltech ft ON f.fueltech_id = ft.code
JOIN fueltech_group ftg on ftg.code = ft.fueltech_group_id
JOIN (
  SELECT
    f_inner.network_region,
    ft_inner.label AS fueltech_label,
    MAX(fs_inner.generated) AS highest_output,
    MIN(fs_inner.generated) AS lowest_output
  FROM facility_scada fs_inner
  JOIN facility f_inner ON fs_inner.facility_code = f_inner.code
  JOIN fueltech ft_inner ON f_inner.fueltech_id = ft_inner.code
  where
    fs_inner.trading_interval >= now() at time zone 'AEST' - interval '180 days' and
    fs_inner.generated >= 0
  GROUP BY f_inner.network_region, ft_inner.code
  ) AS aggr ON f.network_region = aggr.network_region AND ft.label = aggr.fueltech_label
where
    fs.trading_interval >= now() at time zone 'AEST' - interval '180 days' and
    f.network_id in ('AEMO_ROOFTOP', 'NEM', 'WEM')
GROUP BY f.network_id, f.network_region, ftg.code, ftg.label, aggr.highest_output, aggr.lowest_output;
