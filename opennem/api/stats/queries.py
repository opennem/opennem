from datetime import datetime
from typing import List

from opennem.core.normalizers import normalize_duid


def duid_in_case(facility_codes: List[str]) -> str:
    return ",".join(
        ["'{}'".format(i) for i in map(normalize_duid, facility_codes)]
    )



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
        order by 1 desc, 2 asc
    """.format(
        year=year, network_code=network_code
    )
