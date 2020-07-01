import decimal
import json
import os
from datetime import datetime
from pprint import pprint

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
    json_data = wem_power_groups()

    tempratures = bom_observation("009021")
    price = wem_price()
    demand = wem_demand()

    json_data.append(tempratures)
    json_data.append(price)
    json_data.append(demand)

    power_path = BASE_EXPORT + "/power/wem.json"

    with open(
        power_path,
        "w",
        transport_params=dict(multipart_upload_kwargs=UPLOAD_ARGS),
    ) as fh:
        json.dump(json_data, fh, cls=NemEncoder)


def wem_export_years():

    for year in [2020, 2019]:
        json_envelope = []

        energy = wem_energy_year(year)
        market_value = wem_market_value_year(year)

        json_envelope = energy + market_value

        year_path = BASE_EXPORT + f"/wem/energy/daily/{year}.json"

        with open(
            year_path,
            "w",
            transport_params=dict(multipart_upload_kwargs=UPLOAD_ARGS),
        ) as fh:
            json.dump(json_envelope, fh, cls=NemEncoder)


def wem_export_all():

    energy = wem_energy_all()
    market_value = wem_market_value_all()

    json_envelope = energy + market_value

    all_path = BASE_EXPORT + f"/wem/energy/monthly/all.json"

    with open(
        all_path,
        "w",
        transport_params=dict(multipart_upload_kwargs=UPLOAD_ARGS),
    ) as fh:
        json.dump(json_envelope, fh, cls=NemEncoder)


def wem_run_all():
    wem_export_power()
    wem_export_years()
    wem_export_all()


if __name__ == "__main__":
    # j = wem_market_value_year()
    # pprint(json.dumps(j, cls=NemEncoder))

    wem_export_power()
    wem_export_years()
    wem_export_all()
