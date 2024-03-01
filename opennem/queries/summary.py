"""
Daily summary - fueltechs as proportion of demand
and other stats per network query
"""

import logging
from datetime import datetime, timedelta
from textwrap import dedent

from datetime_truncate import truncate as date_trunc

from opennem.queries.utils import list_to_case
from opennem.schema.network import NetworkSchema
from opennem.utils.timezone import is_aware

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
    fs.trading_day as trading_day,
    ftg.code,
    ftg.label,
    ftg.color,
    ft.renewable,
    round(sum(fs.energy), 2) as energy,
    round(max(ftt.generated_total), 2) as generated_total,
    round(max(dt.demand_total), 2) as demand_total,
    round( sum(fs.energy) / max(ftt.generated_total) * 100, 2) as generated_proportion
from at_facility_daily fs
left join facility f on fs.facility_code = f.code
join fueltech ft on f.fueltech_id = ft.code
join fueltech_group ftg on ft.fueltech_group_id = ftg.code
left join dt on dt.trading_day = fs.trading_day
left join ftt on ftt.trading_day = fs.trading_day
where
    fs.trading_day >= '{date_min}'
    and fs.trading_day < '{date_max}'
    and fs.network_id IN ('{network_id}', 'AEMO_ROOFTOP')
    and f.fueltech_id not in ({fueltechs_excluded})
    and f.dispatch_type = 'GENERATOR'
group by 1, 2, 3, 4, 5;
"""


def get_daily_fueltech_summary_query(day: datetime, network: NetworkSchema, fueltechs_excluded: list[str] = None) -> str:
    """Get the fueltech summary query for a day and for a network"""

    # default list of excluded fueltechs
    if fueltechs_excluded is None:
        fueltechs_excluded = ["imports", "exports", "interconnector", "battery_discharging"]

    # If the date doesn't have a timezone apply network timezone
    if not is_aware(day):
        day = day.replace(tzinfo=network.get_fixed_offset())

    # Trunc the date to midnight and add the end of day as max
    date_min = date_trunc(day, truncate_to="day")
    date_max = date_min + timedelta(days=1)

    query = __daily_summary_fueltech_query.format(
        date_min=date_min,
        date_max=date_max,
        tz=network.timezone_database,
        network_id=network.code,
        fueltechs_excluded=list_to_case(fueltechs_excluded),
    )

    return dedent(query)
