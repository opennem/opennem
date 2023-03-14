import pytest

from opennem.core.stations.station_code_from_duids import station_code_from_duids


@pytest.mark.parametrize(
    ["subject", "expected"],
    [
        ([None], None),
        ([""], None),
        ([], None),
        (["BARRON1", "BARRON2"], "BARRON"),
        (["OSBAG"], "OSBAG"),
        (["OSBAG", "OSBAG"], "OSBAG"),
        (["FNWF1"], "FNWF"),
    ],
)
def test_station_code_from_duid(subject: list[str], expected: str) -> None:
    return_val = station_code_from_duids(subject)

    assert expected == return_val, "Got correct response"
