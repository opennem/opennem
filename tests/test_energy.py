import csv
from pathlib import Path
from typing import List

from opennem.core.energy import energy_sum, shape_energy_dataframe
from opennem.schema.network import NetworkNEM

# from opennem.workers.emissions import load_factors

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

    power_df = shape_energy_dataframe(power_results_bw01)

    energy_sum(power_df, NetworkNEM)

    assert len(records) == 32288, "Right length of records"


def test_energy_sum_outputs() -> None:
    records = load_energy_fixture_csv("nem_generated_coal_black.csv")

    assert len(records) == 50, "Has the correct number of records"

    power_df = shape_energy_dataframe(records)

    assert len(power_df) == 50, "Has the correct number of records"

    es = energy_sum(power_df, NetworkNEM)

    # should be 50 records
    assert len(es) == 1536, "Has the correct number of records"

    assert es.eoi_quantity.sum() > 1000, "Has energy value"

    return es
