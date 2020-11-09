import pytest

from opennem.core.network_region_bom_station_map import (
    get_network_region_weather_station,
)


@pytest.mark.parametrize(
    "network_region,weather_station_id",
    [("WEM", "009021"), ("NSW1", "066037"),],
)
def test_get_network_region_weather_station(
    network_region, weather_station_id
):
    date_subject_dt = get_network_region_weather_station(network_region)
    assert date_subject_dt == weather_station_id
