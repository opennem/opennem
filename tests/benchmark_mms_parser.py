from pathlib import Path
from typing import Any

import pytest

from opennem.core.downloader import file_opener
from opennem.core.parsers.aemo.mms import parse_aemo_mms_csv

NEM_FILE_PATH = Path("data/NEM_FACILITY_SCADA_DAY.zip")


def load_nem_scada_records() -> dict[str, Any]:
    csv_content = file_opener(NEM_FILE_PATH).decode("utf-8")

    ts = parse_aemo_mms_csv(csv_content)

    if not ts:
        raise Exception("no table set")

    return ts.get_table("unit_scada").records


@pytest.mark.benchmark(
    group="load_nem_scada_records",
    min_rounds=1,
)
def test_benchmark_generate_facility_scada_base(benchmark) -> None:
    benchmark(load_nem_scada_records)
