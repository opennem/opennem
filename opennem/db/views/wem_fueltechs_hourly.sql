create view wem_fueltechs_hourly as select
        wfs.trading_interval,
        wf.fueltech_id,
        sum(wfs.generated) as gen
    from wem_facility_scada wfs
    left join wem_facility wf on wfs.facility_id = wf.code
    where wf.fueltech_id is not null
    group by wfs.trading_interval, wf.fueltech_id
    order by fueltech_id asc, wfs.trading_interval asc
