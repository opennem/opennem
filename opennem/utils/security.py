""" Security Module """

import random
import string
from urllib.parse import urlparse


def get_random_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def obfuscate_dsn_password(dsn: str) -> str:
    """Takes a DSN string and obfuscates the password"""
    dsn_parsed = urlparse(dsn)

    if dsn_parsed.password:
        host_info = dsn_parsed.netloc.rpartition("@")[-1]

        dsn_parsed = dsn_parsed._replace(netloc=f"{dsn_parsed.username}:*****@{host_info}")

    obfuscated_dsn = dsn_parsed.geturl()

    return obfuscated_dsn
