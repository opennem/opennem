import pytest

from opennem.api.auth.utils import cookie_name_from_auth_name, generate_api_key, header_name_from_auth_name
from opennem.core.validators.strings import string_is_urlsafe


def test_generate_api_key() -> None:
    genkey = generate_api_key(20)

    assert isinstance(genkey, str), "Key is a string"
    assert len(genkey) == 20, "Key has correct length"
    assert string_is_urlsafe(genkey) is True, "Key is url safe"


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
