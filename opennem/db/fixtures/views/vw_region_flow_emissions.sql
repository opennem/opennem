create view vw_region_flow_emissions as select
    f.trading_interval as trading_interval,
    date_trunc('day', f.trading_interval) at time zone 'AEST' as ti_day_aest,
    date_trunc('month', f.trading_interval) at time zone 'AEST' as ti_month_aest,
    f.network_region || '->' || f.interconnector_region_to as flow_region,
    f.network_region as flow_from,
    f.interconnector_region_to as flow_to,
    sum(f.energy) as flow_energy,
    sum(f.energy) * max(efi.emissions_per_mw) as flow_from_emissions,
    sum(f.energy) * max(eti.emissions_per_mw) as flow_to_emissions,
    max(efi.emissions_per_mw) as flow_from_intensity,
    max(eti.emissions_per_mw) as flow_to_intensity
from mv_facility_all f
left join mv_interchange_energy_nem_region ef on ef.trading_interval = f.trading_interval and ef.network_region = f.network_region
left join mv_interchange_energy_nem_region et on et.trading_interval = f.trading_interval and et.network_region = f.interconnector_region_to
left join mv_region_emissions efi on efi.trading_interval = f.trading_interval and efi.network_region = f.network_region
left join mv_region_emissions eti on eti.trading_interval = f.trading_interval and eti.network_region = f.interconnector_region_to
where
    f.interconnector is True
group by 1, 2, 3, flow_region, 5, 6, f.interconnector_region_to
order by trading_interval desc, flow_from asc, flow_to asc;
