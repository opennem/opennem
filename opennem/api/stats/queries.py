from datetime import datetime
from typing import List

from opennem.core.normalizers import normalize_duid


def duid_in_case(facility_codes: List[str]) -> str:
    return ",".join(
        ["'{}'".format(i) for i in map(normalize_duid, facility_codes)]
    )


def wem_energy_facility(
    facility_codes: List[str],
    network_code: str,
    interval: str = "day",
    period: str = "7d",
) -> str:

    network_code = network_code.upper()

    __query = """
        with intervals as (
            select generate_series(
                date_trunc('day', now() AT TIME ZONE 'UTC') - '7 day'::interval,
                date_trunc('day', now() AT TIME ZONE 'UTC'),
                '1 day'::interval
            )::date as interval
        )

        select
            i.interval AS trading_day,
            fs.facility_code as facility_code,
            coalesce(sum(fs.eoi_quantity), NULL) as energy_output
        from intervals i
        left join facility_scada fs on date_trunc('day', fs.trading_interval AT TIME ZONE 'UTC')::date = i.interval
        where
            fs.facility_code in ({facility_codes_parsed})
            and fs.trading_interval > now() AT TIME ZONE 'UTC' - '7 day'::interval
            and fs.network_id = '{network_code}'
        group by 1, 2
        order by 2 asc, 1 asc
    """

    query = __query.format(
        facility_codes_parsed=duid_in_case(facility_codes),
        network_code=network_code,
    )

    return query


def energy_year_network(network_code: str = "WEM", year: int = None) -> str:
    if not year:
        year = datetime.today().year

    network_code = network_code.upper()

    return """
        select
            date_trunc('day', fs.trading_interval) AS trading_day,
            max(fs.eoi_quantity) as energy_output,
            f.fueltech_id as fueltech
        from facility_scada fs
        left join facility f on fs.facility_code = f.code
        where
            f.fueltech_id is not null
            and extract('year' from fs.trading_interval) = {year}
            and fs.network_id = '{network_code}'
        group by 1, f.fueltech_id
        order by 1 asc, 2 asc
    """.format(
        year=year, network_code=network_code
    )
