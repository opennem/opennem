import csv
from pathlib import Path
from typing import Any

import pytest

from opennem.controllers.nem import generate_facility_scada, unit_scada_generate_facility_scada
from opennem.core.downloader import file_opener
from opennem.core.parsers.aemo.mms import parse_aemo_mms_csv
from opennem.schema.network import NetworkWEM

RECORDS_PATH = Path("data/wem/facility-scada-2020-10.csv")
NEM_FILE_PATH = Path("data/NEM_FACILITY_SCADA_DAY.zip")


def load_nem_scada_records() -> dict[str, Any]:
    csv_content = file_opener(NEM_FILE_PATH).decode("utf-8")

    ts = parse_aemo_mms_csv(csv_content)

    if not ts:
        raise Exception("no table set")

    return ts.get_table("unit_scada").records


def load_wem_scada_records(limit: int | None = None, intentional_duplicate: bool = False) -> dict[str, Any]:
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

            if limit and len(records) > limit:
                break

    if intentional_duplicate:
        records.append(records[0])

    return records


test_wem_scada_records = load_wem_scada_records(1000)
test_all_wem_scada_records = load_wem_scada_records()
test_all_wem_scada_records_with_duplicates = load_wem_scada_records(intentional_duplicate=True)

test_nem_large = load_nem_scada_records()


@pytest.mark.benchmark(
    group="facility_scada_parser",
    min_rounds=50,
)
@pytest.mark.parametrize(
    "records,primary_key_track",
    [
        (test_all_wem_scada_records, False),
        (test_all_wem_scada_records, True),
    ],
)
def test_benchmark_generate_facility_scada_base(benchmark, records, primary_key_track):
    benchmark(
        unit_scada_generate_facility_scada,
        records,
        network=NetworkWEM,
        interval_field="Trading Date",
        facility_code_field="Facility Code",
        energy_field="Energy Generated (MWh)",
        power_field="EOI Quantity (MW)",
        # groupby_filter=groupby_filter,
        primary_key_track=primary_key_track,
    )


@pytest.mark.benchmark(
    group="facility_scada_parser",
    min_rounds=50,
)
@pytest.mark.parametrize(
    "records",
    [(test_all_wem_scada_records), (test_all_wem_scada_records_with_duplicates), (test_nem_large)],
)
def test_benchmark_generate_facility_scada_optimized(benchmark, records):
    benchmark(
        generate_facility_scada,
        records,
        network=NetworkWEM,
        interval_field="Trading Date",
        facility_code_field="Facility Code",
        energy_field="Energy Generated (MWh)",
        power_field="EOI Quantity (MW)",
    )
