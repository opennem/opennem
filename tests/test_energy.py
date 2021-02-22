import csv
from pathlib import Path
from typing import List

from opennem.core.energy import energy_sum
from opennem.schema.network import NetworkNEM

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "energy"


def load_energy_fixture_csv(fixture_name: str) -> List:
    fixture_file_path = FIXTURE_PATH / fixture_name

    if not fixture_file_path.is_file():
        raise Exception("Fixture {} not found".format(fixture_name))

    fixture_envelope = None

    with fixture_file_path.open() as fh:
        csvreader = csv.DictReader(fh)
        fixture_envelope = list(csvreader)

    return fixture_envelope


def test_energy_sum_average_fixture() -> None:
    records = load_energy_fixture_csv("power_nem_nsw1_coal_black_1_week.csv")

    power_results_bw01 = list(filter(lambda x: x["facility_code"] == "BW01", records))

    es = energy_sum(power_results_bw01, NetworkNEM)

    assert len(records) == 32288, "Right length of records"
