import clickhouse_connect

from opennem import settings

if not settings.clickhouse_url:
    raise ValueError("Clickhouse URL not set")

print(f"Connecting to Clickhouse at {settings.clickhouse_url} {settings.clickhouse_url.path[1:]}")
ch_client = clickhouse_connect.get_client(
    host=settings.clickhouse_url.host, port=settings.clickhouse_url.port, database=settings.clickhouse_url.path[1:]
)
