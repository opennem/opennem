""""
OpenNEM Data Validators

"""

from datetime import datetime, timedelta

from datedelta import datedelta

from opennem.api.stats.schema import ValidNumber, load_opennem_dataset_from_file
from opennem.utils.dates import num_intervals_between_datetimes
from opennem.utils.tests import TEST_FIXTURE_PATH


def validate_data_outputs(
    series: list[ValidNumber],
    interval_size: timedelta | datedelta,
    start_date: datetime,
    end_date: datetime,
) -> bool:
    """
    Checks that the series has the correct length considering start and end date and the series edge type
    """
    number_of_intervals = num_intervals_between_datetimes(interval_size, start_date, end_date)

    if len(series) != number_of_intervals:
        raise Exception(f"validate_data_outputs: Got {len(series)} intervals, expected {number_of_intervals}")

    return True


if __name__ == "__main__":
    power_series = load_opennem_dataset_from_file(TEST_FIXTURE_PATH / "nem_nsw1_7d.json")
    energy_series = load_opennem_dataset_from_file(TEST_FIXTURE_PATH / "nem_nsw1_1y.json")

    for id in power_series.ids:
        print(id)

    ids_to_test = [
        "au.nem.nsw1.fuel_tech.wind.energy",
        "au.nem.nsw1.fuel_tech.wind.market_value",
        "au.nem.nsw1.fuel_tech.coal_black.emissions",
        "au.nem.nsw1.demand.energy",
        "au.nem.nsw1.demand.market_value",
        "au.nem.nsw1.fuel_tech.imports.energy",
        "au.nem.nsw1.fuel_tech.exports.emissions",
        "au.nem.nsw1.fuel_tech.imports.market_value",
        "au.nem.nsw1.temperature_mean",
        "au.nem.nsw1.temperature_min",
    ]

    for id in ids_to_test:
        test_case = energy_series.get_id(id)

        if not test_case:
            print(f"{id} not found")
            continue

        test_case_history = test_case.history

        assert (
            validate_data_outputs(
                test_case_history.data,
                test_case_history.get_interval(),
                test_case_history.start,
                test_case_history.last,
                SeriesEdgeType.rails,
            )
            == True
        )
