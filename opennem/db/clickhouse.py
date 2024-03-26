import logging

import clickhouse_connect

# from clickhouse_connect import Cli
from clickhouse_connect.driver.client import Client as ClickhouseClient
from pydantic import AnyUrl

from opennem import settings

logger = logging.getLogger("opennem.db.clickhouse")

if not settings.clickhouse_url:
    raise ValueError("Clickhouse URL not set")


def clickhouse_client_factory(host_url: AnyUrl) -> ClickhouseClient:
    params_dict = {}

    if host_url.username:
        params_dict["username"] = host_url.username

    if host_url.password:
        params_dict["password"] = host_url.password

    if host_url.host:
        params_dict["host"] = host_url.host

    if host_url.port:
        params_dict["port"] = host_url.port

    if host_url.path:
        params_dict["database"] = host_url.path[1:]

    ch_client = clickhouse_connect.get_client(**params_dict)

    return ch_client


ch_client = clickhouse_client_factory(settings.clickhouse_url)

if __name__ == "__main__":
    print(ch_client.ping())
