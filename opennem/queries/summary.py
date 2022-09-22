"""
Daily summary - fueltechs as proportion of demand
and other stats per network
"""
import logging
from datetime import datetime, timedelta
from operator import attrgetter
from textwrap import dedent
from typing import List

from datetime_truncate import truncate as date_trunc

from opennem.core.templates import serve_template
from opennem.db import get_database_engine
from opennem.notifications.slack import slack_message
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.settings import settings  # noqa: F401
from opennem.utils.dates import DATE_YESTERDAY
from opennem.utils.sql import duid_in_case

logger = logging.getLogger("opennem.workers.daily_summary")


__daily_summary_fueltech_query = """
with

dt as (select
    date_trunc('day', bs.trading_interval at time zone '{tz}') as trading_day,
    bs.network_id,
    sum(bs.demand_total) as demand_total
from balancing_summary bs
where
    bs.trading_interval >= '{date_min}'
    and bs.trading_interval < '{date_max}'
    and bs.network_id='{network_id}'
group by 1, 2
order by 1 desc),

ftt as (select
    date_trunc('day', fs.trading_interval at time zone '{tz}') as trading_day,
--    fs.network_id,
    sum(fs.eoi_quantity) as generated_total
from facility_scada fs
left join facility f on f.code = fs.facility_code
where
    fs.trading_interval >= '{date_min}'
    and fs.trading_interval < '{date_max}'
    and fs.network_id IN ('{network_id}', 'AEMO_ROOFTOP')
    and f.fueltech_id not in ('imports', 'exports', 'interconnector', 'battery_discharging')
    and f.dispatch_type = 'GENERATOR'
group by 1
order by 1 desc)

select
    date_trunc('day', fs.trading_interval at time zone '{tz}') as trading_day,
    fs.network_id,
    f.fueltech_id,
    ft.label,
    ft.renewable,
    round(sum(fs.eoi_quantity), 2) as energy,
    round(max(ftt.generated_total), 2) as generated_total,
    round(max(dt.demand_total), 2) as demand_total,
    round( sum(fs.eoi_quantity) / max(ftt.generated_total) * 100, 2) as generated_proportion
from facility_scada fs
left join facility f on fs.facility_code = f.code
join fueltech ft on f.fueltech_id = ft.code
left join dt on dt.trading_day = date_trunc('day', fs.trading_interval at time zone '{tz}')
left join ftt on ftt.trading_day = date_trunc('day', fs.trading_interval at time zone '{tz}')
where
    fs.trading_interval >= '{date_min}'
    and fs.trading_interval < '{date_max}'
    and fs.network_id IN ('{network_id}', 'AEMO_ROOFTOP')
    and f.fueltech_id not in ({fueltechs_excluded})
    and f.dispatch_type = 'GENERATOR'
group by 1, 3, 2, 4, 5;
"""


def get_daily_fueltech_summary_query(day: datetime = DATE_YESTERDAY, network: NetworkSchema = NetworkNEM) -> str:
    EXCLUDE_FUELTECHS = ["imports", "exports", "interconnector", "battery_discharging"]

    day_date = day.replace(tzinfo=network.get_fixed_offset())

    date_min = date_trunc(day_date, truncate_to="day")
    date_max = date_min + timedelta(days=1)

    query = __daily_summary_fueltech_query.format(
        date_min=date_min,
        date_max=date_max,
        tz=network.timezone_database,
        network_id=network.code,
        fueltechs_excluded=duid_in_case(EXCLUDE_FUELTECHS),
    )

    return dedent(query)
