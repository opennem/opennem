""" Security Module """

from urllib.parse import urlparse


def obfuscate_dsn_password(dsn: str) -> str:
    """Takes a DSN string and obfuscates the password"""
    dsn_parsed = urlparse(dsn)

    if dsn_parsed.password:
        host_info = dsn_parsed.netloc.rpartition("@")[-1]

        dsn_parsed = dsn_parsed._replace(
            netloc="{}:*****@{}".format(dsn_parsed.username, host_info)
        )

    obfuscated_dsn = dsn_parsed.geturl()

    return obfuscated_dsn
