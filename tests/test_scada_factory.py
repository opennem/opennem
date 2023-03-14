import json
from datetime import datetime, timedelta

from opennem.api.stats.controllers import stats_factory
from opennem.api.stats.schema import DataQueryResult, OpennemData, OpennemDataSet
from opennem.api.time import human_to_interval, human_to_period
from opennem.core.networks import network_from_network_code
from opennem.core.units import get_unit
from opennem.utils.dates import is_valid_isodate


def get_power_example() -> OpennemDataSet:
    network = network_from_network_code("NEM")
    interval = human_to_interval("5m")
    units = get_unit("power")
    human_to_period("7d")
    network_region_code = "NSW1"

    test_rows = []

    dt = datetime.fromisoformat("2021-01-15 10:00:00")

    for ft in ["coal_black", "coal_brown"]:
        for v in range(0, 3):
            test_rows.append([dt, ft, v])
            dt = dt + timedelta(minutes=5)

    stats = [DataQueryResult(interval=i[0], result=i[2], group_by=i[1] if len(i) > 1 else None) for i in test_rows]

    assert len(stats) == 6, "Should have 6 stats"

    result = stats_factory(
        stats,
        code=network_region_code or network.code,
        network=network,
        interval=interval,
        units=units,
        region=network_region_code,
        fueltech_group=True,
    )

    if not result:
        raise Exception("Bad unit test data")

    return result


def test_power_is_valid() -> None:
    result = get_power_example()
    assert isinstance(result, OpennemDataSet), "Returns a dataset"


def test_power_has_version() -> None:
    result = get_power_example()
    assert hasattr(result, "version"), "Result has version"


def test_power_has_created_date() -> None:
    result = get_power_example()
    assert hasattr(result, "created_at"), "Resut has created at attribute"


def test_power_has_network_id() -> None:
    result = get_power_example()
    assert hasattr(result, "network"), "Resut has network attribute"
    assert result.network == "nem", "Correct network set"


def test_power_valid_created_date() -> None:
    """Test valid ISO creted date"""
    result = get_power_example()
    result_json = result.json(indent=4)

    r = json.loads(result_json)

    assert is_valid_isodate(r["created_at"]), "Created at is valid ISO date"


def test_power_has_data() -> None:
    result = get_power_example()
    assert hasattr(result, "data"), "Resultset has data"

    # satisfy mypy
    if not result.data:
        raise Exception("Invalid test data")

    data = result.data

    assert len(data) == 2, "Has two data series"


def test_power_data_series() -> None:
    result = get_power_example()

    for data_set in result.data:
        assert isinstance(data_set, OpennemData), "Data set is a valid data set schema"
        assert hasattr(data_set, "id"), "Has an id"
        assert hasattr(data_set, "type"), "Has a type attribute"
        assert hasattr(data_set, "units"), "Has units attribute"
        assert hasattr(data_set, "history"), "Has history"

        # check history
        assert hasattr(data_set.history, "start"), "Has a start date"
        assert hasattr(data_set.history, "last"), "Has a last date"
        assert hasattr(data_set.history, "interval"), "Has an interval"

        interval = data_set.history.interval

        assert interval == "5m", "Has the correct interval"

        data_values = data_set.history.data

        assert len(data_values) == 3, "Should have 3 values"


def test_power_returns_json() -> None:
    result = get_power_example()
    result_json = result.json(indent=4)

    r = json.loads(result_json)

    assert isinstance(r, dict), "JSON is a dict"
    assert "version" in r, "Has a version string"
