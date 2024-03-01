"""
Daily summary - fueltechs as proportion of demand
and other stats per network
"""

import logging
from datetime import datetime, timedelta
from textwrap import dedent

from datetime_truncate import truncate as date_trunc

from opennem import settings  # noqa: F401
from opennem.queries.utils import duid_to_case, list_to_sql_in_condition
from opennem.schema.network import NetworkNEM, NetworkSchema
from opennem.utils.dates import DATE_YESTERDAY

logger = logging.getLogger("opennem.queries.tod")


__daily_summary_fueltech_query = """
with

demand_per_interval as (select
    bs.trading_interval at time zone '{tz}' as trading_interval,
    bs.network_id,
    sum(bs.demand_total) as demand_total
from balancing_summary bs
where
    bs.trading_interval >= '{date_min}'
    and bs.trading_interval < '{date_max}'
    and bs.network_id IN ({networks})
group by 1, 2
order by 1 desc),

generated_per_interval as (select
    fs.trading_interval at time zone 'AEST' as trading_interval,
    sum(fs.generated) as generated_total
from facility_scada fs
left join facility f on f.code = fs.facility_code
where
    fs.trading_interval >= '{date_min}'
    and fs.trading_interval < '{date_max}'
    and fs.network_id IN ({networks})
    and f.fueltech_id not in ({fueltechs_excluded})
    and f.dispatch_type = 'GENERATOR'
group by 1
order by 1 desc)

select
    fs.trading_interval at time zone '{tz}' as trading_interval,
    fs.network_id,
    ftg.code as fueltech_group,
    ftg.label,
    ft.renewable,
    round(sum(fs.generated), 2) as generated,
    round(max(generated_per_interval.generated_total), 2) as generated_total,
    round(max(demand_per_interval.demand_total) / 12, 2) as demand_total,
    round( sum(fs.generated) / max(generated_per_interval.generated_total) * 100, 2) as generated_proportion
from facility_scada fs
left join facility f on fs.facility_code = f.code
join fueltech ft on f.fueltech_id = ft.code
join fueltech_group ftg on ft.fueltech_group_id = ftg.code
left join demand_per_interval on demand_per_interval.trading_interval = fs.trading_interval at time zone '{tz}'
left join generated_per_interval on generated_per_interval.trading_interval = fs.trading_interval at time zone '{tz}'
where
    fs.trading_interval >= '{date_min}'
    and fs.trading_interval < '{date_max}'
    and fs.network_id IN ({networks})
    and f.fueltech_id not in ({fueltechs_excluded})
    and f.dispatch_type = 'GENERATOR'
group by 1, 2, 3, 4, 5
order by 1 desc;
"""


def get_time_of_day_query(day: datetime = DATE_YESTERDAY, network: NetworkSchema = NetworkNEM) -> str:
    EXCLUDE_FUELTECHS = ["imports", "exports", "interconnector", "battery_discharging"]

    day_date = day.replace(tzinfo=network.get_fixed_offset())

    date_min = date_trunc(day_date, truncate_to="day")
    date_max = date_min + timedelta(days=1)

    query = __daily_summary_fueltech_query.format(
        date_min=date_min,
        date_max=date_max,
        tz=network.timezone_database,
        networks=list_to_sql_in_condition([i.code for i in network.get_networks_query()]),
        fueltechs_excluded=duid_to_case(EXCLUDE_FUELTECHS),
    )

    return dedent(query)


if __name__ == "__main__":
    print(get_time_of_day_query())
