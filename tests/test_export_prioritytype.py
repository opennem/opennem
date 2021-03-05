import pytest

from opennem.api.export.map import PriorityType, priority_from_name


def test_priority_from_name() -> None:
    priority_lookup = priority_from_name("live")

    assert isinstance(priority_lookup, PriorityType), "Returns a PriorityType"
    assert priority_lookup == PriorityType.live, "Returns correct type"


def test_priority_from_name_notfound() -> None:
    with pytest.raises(Exception) as exinfo:
        priority_from_name("__doesnt_exist__")

    assert "Could not find priority" in str(exinfo), "Correct error"
