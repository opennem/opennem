import pytest

from opennem.api.auth.utils import (
    cookie_name_from_auth_name,
    generate_api_key,
    header_name_from_auth_name,
)


@pytest.mark.parametrize(
    ["auth_name", "expected_cookie_name"],
    [("onaa", "_onaa"), ("ONAA", "_onaa"), ("_onaa", "_onaa")],
)
def test_cookie_name_from_auth_name(auth_name: str, expected_cookie_name: str) -> None:
    cookie_name = cookie_name_from_auth_name(auth_name)

    assert cookie_name == expected_cookie_name, "Cookie generated value not expected"


@pytest.mark.parametrize(
    ["auth_name", "expected_header_name"],
    [("onaa", "X-ONAA")],
)
def test_header_name_from_auth_name(auth_name: str, expected_header_name: str) -> None:
    cookie_name = header_name_from_auth_name(auth_name)

    assert cookie_name == expected_header_name, "Cookie generated value not expected"
