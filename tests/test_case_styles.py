import pytest

from opennem.core.normalizers import blockwords_to_snake_case


@pytest.mark.parametrize(
    ["subject", "expected_result"],
    [
        ("SETTLEMENTDATE", "settlement_date"),
        ("NETINTERCHANGE", "net_interchange"),
        ("interchange", "interchange"),
        ("PERIODTYPE", "period_type"),
        ("PERIOD TYPE", "period_type"),
        ("PERIOD_TYPE", "period_type"),
        (" PERIOD TYPE ", "period_type"),
        (" period TYPE ?!@", "period_type"),
        ("region", "region"),
        ("regionid", "region_id"),
        ("totaldemand", "total_demand"),
        ("SEMISCHEDULEDGENERATION", "semi_scheduled_generation"),
        ("RRP", "rrp"),
    ],
)
def test_blockwords_to_snake_case(subject: str, expected_result: str) -> None:
    words_return = blockwords_to_snake_case(subject)
    assert words_return == expected_result, "Words match"
