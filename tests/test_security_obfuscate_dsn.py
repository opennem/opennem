import pytest

from opennem.utils.security import obfuscate_dsn_password


@pytest.mark.parametrize(
    ["dsn_subject", "dsn_expected"],
    [
        (
            "postgresql://user:password@localhost:5555/db",
            "postgresql://user:*****@localhost:5555/db",
        ),
        ("postgresql://user@localhost:5555/db", "postgresql://user@localhost:5555/db"),
        ("https://user:password@test.com", "https://user:*****@test.com"),
        ("https://user@test.com", "https://user@test.com"),
        ("https://test.com", "https://test.com"),
    ],
)
def test_obfuscate_dsn_password(dsn_subject: str, dsn_expected: str) -> None:
    dsn_result = obfuscate_dsn_password(dsn_subject)
    assert dsn_result == dsn_expected, "DSN string correctly obfuscated"
