"""
OpenNEM Monitor emission factors for facilities

"""
import logging
from typing import List, Optional

from opennem.db import get_database_engine
from opennem.schema.core import BaseConfig

# from opennem.notifications.slack import slack_message

logger = logging.getLogger("opennem.monitors.facility_seen")


class FacilityEmissionsRecord(BaseConfig):
    station_name: str
    network_id: str
    network_region: str
    facility_code: str
    emissions_factor_co2: Optional[float] = None
    fueltech_id: str


def get_facility_no_emission_factor() -> List[FacilityEmissionsRecord]:
    """Run this and it'll check if there are new facilities in
    that don't have emission factors
    """

    engine = get_database_engine()

    __query = """
        select
            s.name,
            f.network_id,
            f.network_region,
            f.code,
            f.emissions_factor_co2,
            f.fueltech_id
        from facility f
        left join station s on f.station_id = s.id
        left join fueltech ft on f.fueltech_id = ft.code
        where
            ft.renewable is False and
            ft.code not in ('imports', 'exports') and
            (f.emissions_factor_co2 is null or f.emissions_factor_co2 is 0) and
            and f.status_id='operating'
        order by network_region desc;
    """

    with engine.connect() as c:
        logger.debug(__query)
        row = list(c.execute(__query))

    records: List[FacilityEmissionsRecord] = [
        FacilityEmissionsRecord(
            station_name=r[0],
            network_id=r[1],
            network_region=r[2],
            facility_code=r[3],
            emissions_factor_co2=r[4],
            fueltech_id=r[5],
        )
        for r in row
    ]

    return records


if __name__ == "__main__":
    r = get_facility_no_emission_factor()
    print(r)
