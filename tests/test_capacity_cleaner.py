from opennem.core.normalizers import clean_capacity


class TestCapacityCleaner(object):
    def test_capacity_blank(self):
        subject = clean_capacity("")
        assert type(subject) is type(None), "Blank string should be nonetype"
        assert subject == None, "Blank capacity should be none"

    def test_capacity_string_excel_blank(self):
        subject = clean_capacity("-")
        assert type(subject) is type(None), "Blank string should be nonetype"
        assert subject == None, "Blank capacity should be none"

    def test_capacity_zero_string(self):
        subject = clean_capacity("0")
        assert type(subject) is float, "Capacity should be a float"
        assert subject == 0.0, "0 string capacity should be float 0"

    def test_capacity_zero(self):
        subject = clean_capacity(0)
        assert type(subject) is float, "Capacity should be a float"
        assert subject == 0.0, "0 string capacity should be float 0"

    def test_capacity_zero__string_padded(self):
        subject = clean_capacity("0  ")
        assert type(subject) is float, "Capacity should be a float"
        assert subject == 0.0, "0 string capacity should be float 0"

    def test_capacity_postive_value(self):
        subject = clean_capacity("1.1")
        assert type(subject) is float, "Capacity should be a float"
        assert subject == 1.1, "0 string capacity should be float 0"

    def test_capacity_rounding(self):
        subject = clean_capacity("1.00000001")
        assert type(subject) is float, "Capacity should be a float"
        assert subject == 1.0, "0 string capacity should be rounded to 1"

    def test_capacity_range(self):
        subject = clean_capacity(" 193.76 - 204.4 ")

        assert (
            subject == 204.4
        ), "Parse capacity ranges to default to get maximum"
