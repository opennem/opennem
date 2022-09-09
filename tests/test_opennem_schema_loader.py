import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from opennem.api.stats.loader import load_statset


def get_fixture(name: str) -> Dict:

    f = Path(__file__).parent / "fixtures" / name

    if not f.is_file():
        raise Exception(f"Fixture {name} not found")

    with f.open() as fh:
        json_return = json.load(fh)

    return json_return


def test_schema_loader() -> None:
    fixture = get_fixture("power-nsw1.json")

    a = load_statset(fixture)

    print(a.version)

    assert isinstance(a.version, str), "Has a version"
    assert isinstance(a.created_at, datetime), "Has a created date"
    assert len(a.data) == 2, "Has data"

    assert isinstance(a.data[0].history.start, datetime), "Has history and a start date"

    assert a.data[0].id == "nem.nsw1.fuel_tech.coal_black.power", "Has an id"
    assert a.data[0].id_v2() == "nsw1.fuel_tech.black_coal.power", "Has correct v2 id"

    values = a.data[0].history.values()

    assert len(values) == 3, "Has 3 generated values"
