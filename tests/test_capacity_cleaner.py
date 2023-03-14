from typing import Any

from opennem.core.normalizers import clean_capacity


def is_none(subject: Any) -> bool:
    return isinstance(subject, type(None))


class TestCapacityCleaner:
    def test_capacity_blank(self) -> None:
        subject = clean_capacity("")
        assert is_none(subject), "Blank string should return None"

    def test_capacity_none(self) -> None:
        subject = clean_capacity(None)
        assert is_none(subject), "None should return None"

    def test_capacity_string_excel_blank(self) -> None:
        subject = clean_capacity("-")
        assert is_none(subject), "Blank string should return None"

    def test_capacity_zero_string(self) -> None:
        subject = clean_capacity("0")
        assert isinstance(subject, float), "Capacity should be a float"
        assert subject == 0.0, "0 string capacity should be float 0"

    def test_capacity_zero(self) -> None:
        subject = clean_capacity(0)
        assert isinstance(subject, float), "Capacity should be a float"
        assert subject == 0.0, "0 string capacity should be float 0"

    def test_capacity_float(self) -> None:
        value = 204.4
        subject = clean_capacity(value)

        assert value == subject, "Floats return floats"

    def test_capacity_zero__string_padded(self):
        subject = clean_capacity("0  ")
        assert type(subject) is float, "Capacity should be a float"
        assert subject == 0.0, "0 string capacity should be float 0"

    def test_capacity_postive_value(self):
        subject = clean_capacity("1.1")
        assert type(subject) is float, "Capacity should be a float"
        assert subject == 1.1, "0 string capacity should be float 0"

    def test_capacity_string_rounding(self):
        subject = clean_capacity("1.00000001")
        assert type(subject) is float, "Capacity should be a float"
        assert subject == 1.0, "0 string capacity should be rounded to 1"

    def test_capacity_range(self):
        subject = clean_capacity(" 193.76 - 204.4 ")

        assert subject == 204.4, "Parse capacity ranges to default to get maximum"
