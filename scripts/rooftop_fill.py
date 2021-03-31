#!/usr/bin/env python

from opennem.db import get_database_engine

__query = """
insert into facility_scada
select
    'opennem.importer.apvi' as created_by,
    now() as created_at,
    now() as updated_at,
    'NEM' as network_id,
    time_bucket_gapfill('30 minutes', fs.trading_interval) as trading_interval,
    'ROOFTOP_NEM_' ||  rtrim(f.network_region, '1') as facility_code,
    avg(fs.generated) as generated,
    avg(fs.generated) / 2 as eoi_quantity,
    FALSE as is_forecast,
    0 as energy_quality_flag

left join facility f on fs.facility_code = f.code
where
    fs.trading_interval < '2018-03-06 00:00:00+00' and
    fs.trading_interval > '2015-03-19 00:00:00+00' and
    fs.network_id='APVI' and
    f.network_region != 'WEM'
group by 5, 4, 3, 2, 1, 6
order by 6 desc
on conflict do nothing;
"""

if __name__ == "__main__":
    engine = get_database_engine()

    with engine.connect() as c:
        c.execute(__query)
