import csv
from itertools import groupby
from pathlib import Path

import pytest

from opennem.controllers.nem import unit_scada_generate_facility_scada
from opennem.schema.network import NetworkWEM

RECORDS_PATH = Path("data/wem/facility-scada-2020-10.csv")


def load_wem_scada_records(limit: int = 1000):
    records = []

    fieldnames = [
        "Trading Date",
        "Interval Number",
        "Trading Interval",
        "Participant Code",
        "Facility Code",
        "Energy Generated (MWh)",
        "EOI Quantity (MW)",
        "Extracted At",
    ]
    with RECORDS_PATH.open() as fh:
        csvreader = csv.DictReader(fh, fieldnames=fieldnames)
        for record in csvreader:
            if record["Trading Date"] == "Trading Date":
                continue

            records.append(record)

            if len(records) > limit:
                break

    return records


test_wem_scada_records = load_wem_scada_records()


@pytest.mark.benchmark(
    group="facility_scada_parser",
    min_rounds=50,
)
@pytest.mark.parametrize(
    "records,groupby_filter,primary_key_track",
    [
        (test_wem_scada_records, False, False),
        (test_wem_scada_records, False, True),
        (test_wem_scada_records, True, False),
    ],
)
def test_benchmark_generate_facility_scada_base(
    benchmark, records, groupby_filter, primary_key_track
):
    benchmark(
        unit_scada_generate_facility_scada,
        records,
        network=NetworkWEM,
        interval_field="Trading Interval",
        facility_code_field="Facility Code",
        energy_field="Energy Generated (MWh)",
        power_field="EOI Quantity (MW)",
        # groupby_filter=groupby_filter,
        primary_key_track=primary_key_track,
    )
