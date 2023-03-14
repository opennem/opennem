import json
from datetime import datetime
from pathlib import Path

from opennem.core.parsers.aemo.viz import AEMO_5MIN_RESPONSE_KEY, aemo_parse_5min_api

FIXTURE_PATH = Path(__file__).parent / "fixtures"


def load_5min_fixture() -> dict:
    fixture_file_path = FIXTURE_PATH / "aemo_5min_data.json"

    if not fixture_file_path.is_file():
        raise Exception(f"Fixture {fixture_file_path} not found")

    fixture_envelope = None

    with fixture_file_path.open() as fh:
        fixture_envelope = json.load(fh)

    return fixture_envelope


def test_aemo_5min_parser() -> None:
    aemo_data = load_5min_fixture()

    # data looks ok
    assert len(aemo_data[AEMO_5MIN_RESPONSE_KEY]) == 2880, "Correct number of records"

    model_list = aemo_parse_5min_api(aemo_data)

    # sanity check data
    assert len(model_list) == 2880, "Correct number of records"

    min_date = min([i.settlement_date for i in model_list])
    max_date = max([i.settlement_date for i in model_list])

    assert min_date == datetime.fromisoformat("2021-10-06T15:00:00"), "Min date is correct"
    assert max_date == datetime.fromisoformat("2021-10-08T14:55:00"), "Max date is correct"

    # check every field has an rrp
    rrps = [i.rrp for i in model_list if i.rrp > -1000.0]
    assert len(rrps) == 2880, "Have an RRP for every field"

    # test a single model
    single_model = model_list.pop()

    assert single_model.rrp > -1000.0, "Price is ok"
    assert single_model.scheduled_generation > -1000.0, "Scheduled generation seems sane"
    assert single_model.total_demand > -1000.0, "Total demand is sane"
