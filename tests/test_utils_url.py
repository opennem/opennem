import pytest

from opennem.utils.url import strip_query_string


@pytest.mark.parametrize(
    ["url", "url_expected"],
    [
        ("https://www.test.com/test?q=1", "https://www.test.com/test"),
        ("https://www.test.com/test?q=1b=2", "https://www.test.com/test"),
    ],
)
def test_strip_query_string(url: str, url_expected: str) -> None:
    url_subject = strip_query_string(url)

    assert url_subject == url_expected, "URL has stripped query string"
