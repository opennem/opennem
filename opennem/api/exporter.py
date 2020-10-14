import decimal
import json
import os
from datetime import datetime

from smart_open import open

from opennem.api.controllers import (
    bom_observation,
    wem_demand,
    wem_energy_all,
    wem_energy_year,
    wem_market_value_all,
    wem_market_value_year,
    wem_power_groups,
    wem_price,
)
from opennem.api.stats.queries import energy_network_fueltech_year
from opennem.api.stats.router import (
    energy_network_fueltech_api,
    power_network_fueltech_api,
    price_network_region_api,
)
from opennem.db import get_database_engine

YEAR_MIN = 2010

BASE_EXPORT = "s3://data.opennem.org.au"

BASE_EXPORT_LOCAL = os.path.realpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data")
)


class NemEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super(NemEncoder, self).default(o)


UPLOAD_ARGS = {
    "ContentType": "application/json",
}


def wem_export_power():
    engine = get_database_engine()

    stat_set = power_network_fueltech_api(
        network_code="WEM",
        network_region="WEM",
        interval="30m",
        period="7d",
        engine=engine,
    )
    # json_data = wem_power_groups()

    # tempratures = bom_observation("009021")

    price = price_network_region_api(
        engine=engine,
        network_code="WEM",
        region_code="WEM",
        interval="30m",
        period="7d",
    )

    # demand = wem_demand()

    # stat_set.data.append(tempratures)
    stat_set.data = stat_set.data + price.data
    # stat_set.data.append(demand)

    power_path = BASE_EXPORT + "/power/wem.json"
    # power_path = "wem.json"

    with open(
        power_path,
        "w",
        transport_params=dict(multipart_upload_kwargs=UPLOAD_ARGS),
    ) as fh:
        fh.write(stat_set.json())


def wem_export_years():
    engine = get_database_engine()

    for year in range(datetime.now().year, YEAR_MIN - 1, -1):

        stat_set = energy_network_fueltech_api(
            network_code="WEM",
            network_region="WEM",
            interval="1d",
            year=year,
            period="1Y",
            engine=engine,
        )

        # market_value = wem_market_value_year(year)

        year_path = BASE_EXPORT + f"/wem/energy/daily/{year}.json"

        with open(
            year_path,
            "w",
            transport_params=dict(multipart_upload_kwargs=UPLOAD_ARGS),
        ) as fh:
            fh.write(stat_set.json())


def wem_export_all():

    engine = get_database_engine()

    stat_set = energy_network_fueltech_api(
        network_code="WEM",
        network_region="WEM",
        interval="1M",
        period="10Y",
        engine=engine,
    )

    # market_value = wem_market_value_all()

    all_path = BASE_EXPORT + "/wem/energy/monthly/all.json"

    with open(
        all_path,
        "w",
        transport_params=dict(multipart_upload_kwargs=UPLOAD_ARGS),
    ) as fh:
        fh.write(stat_set.json())


def wem_run_all():
    wem_export_power()
    wem_export_years()
    wem_export_all()


if __name__ == "__main__":
    wem_export_power()
    wem_export_years()
    wem_export_all()
