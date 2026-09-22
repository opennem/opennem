"""
OpenNEM Settings Schema

Everything that can be changed is set here and can be overwritten with ENV settings
"""

from datetime import UTC
from datetime import timezone as pytimezone
from pathlib import Path

from pydantic import AliasChoices, AnyUrl, Field, RedisDsn, field_validator
from pydantic_settings import BaseSettings

from opennem.schema.field_types import URLNoPath

SUPPORTED_LOG_LEVEL_NAMES = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class SettingsException(Exception):
    pass


class OpennemSettings(BaseSettings):
    env: str = "local"

    log_level: str = "DEBUG"

    timezone: pytimezone | str = UTC

    # Set maintenance mode - workers won't run and API will return a MaintenanceMode response
    maintenance_mode: bool = False

    db_url: str = Field("postgresql://user:pass@127.0.0.1:15444/opennem", validation_alias=AliasChoices("DATABASE_HOST_URL"))

    clickhouse_url: AnyUrl = Field(
        "clickhouse://localhost:9000/opennem",
        validation_alias=AliasChoices("CLICKHOUSE_URL"),
        description="ClickHouse connection URL in format clickhouse:// schema url",
    )

    # Per-query ClickHouse limits applied on the serving path (execute_async) so a single
    # expensive API query cannot exhaust server memory and trip the server-wide overcommit
    # tracker (Code 241), which would kill unrelated concurrent queries. Backfills use the
    # sync client directly and are unaffected. Set to 0 to disable a given limit.
    clickhouse_query_max_memory_usage: int = Field(
        8_589_934_592,  # 8 GiB
        description="ClickHouse max_memory_usage (bytes) for serving-path queries. 0 = unset.",
    )
    clickhouse_query_max_bytes_before_external_group_by: int = Field(
        4_294_967_296,  # 4 GiB — roughly half of max_memory_usage so GROUP BY spills to disk
        description="ClickHouse max_bytes_before_external_group_by (bytes) for serving-path queries. 0 = unset.",
    )
    clickhouse_query_max_execution_time: int = Field(
        90,
        description="ClickHouse max_execution_time (seconds) for serving-path queries. 0 = unset.",
    )

    redis_url: RedisDsn = Field(
        RedisDsn("redis://127.0.0.1"),
        validation_alias=AliasChoices("REDIS_HOST_URL", "cache_url"),
    )

    # if we're doing a dry run
    dry_run: bool = False

    # API server settings
    api_server_host: str = "0.0.0.0"
    api_server_port: int = 8000
    api_server_workers: int = 1

    # api messages
    api_messages: list[str] = [
        "OpenNEM API has migrated to require authentication. Please see the discssion at https://github.com/opennem/opennem/discussions/243"
    ]

    # percentage of old API requests to return deprecation messages
    api_deprecation_proportion: int = 0

    # throttle rate of api
    api_throttle_rate: float = 0

    # API Dev key
    api_dev_key: str | None = None

    # Internal/enterprise key: recognised in every environment (dev + prod) and
    # granted full enterprise+admin access, bypassing Unkey/Clerk and data limits.
    # Distinct from api_dev_key (which is per-env) so one internal key works everywhere.
    api_internal_key: str | None = None

    # webhooks
    webhook_secret: str | None = None

    # sentry DSN for error reporting
    sentry_url: str | None = None
    # fraction of requests/jobs sent to Sentry as performance traces (0-1)
    sentry_traces_sample_rate: float = 0.05

    # Slack notifications (incoming webhooks — one-way)
    slack_notifications: bool = True
    slack_hook_new_facilities: str | None = None
    slack_hook_monitoring: str | None = None
    slack_hook_feedback: str | None = None
    slack_hook_platform_alerts: str | None = None
    slack_hook_aemo_market_notices: str | None = None
    slack_hook_records: str | None = None
    slack_admin_alert: list[str] | None = ["nik"]

    # Slack App (for interactive buttons — weekly summary approval)
    slack_bot_token: str | None = None
    slack_signing_secret: str | None = None
    slack_weekly_summary_channel: str | None = None

    # LinkedIn API
    linkedin_access_token: str | None = None
    linkedin_organization_id: str | None = None

    # R2 settings
    s3_access_key_id: str | None = Field(None, description="The access key ID for the S3 bucket")
    s3_secret_access_key: str | None = Field(None, description="The secret access key for the S3 bucket")
    s3_bucket_name: str = Field("opennem-dev", description="The name of the S3 bucket")
    s3_endpoint_url: URLNoPath = Field(
        "https://17399e149aeaa08c0c7bbb15382fa5c3.r2.cloudflarestorage.com",
        description="The endpoint URL for the S3 bucket",
    )
    s3_bucket_public_url: URLNoPath = Field("https://data.opennem.org.au", description="The public URL of the S3 bucket")
    s3_region: str = "apac"

    # show database debug
    db_debug: bool = False

    # timeout on http requests
    # see opennem.utils.http
    http_timeout: int = 20

    # number of retries by default
    http_retries: int = 5

    # cache http requests locally
    http_verify_ssl: bool = True
    http_proxy_url: str | None = None  # @note don't let it confict with env HTTP_PROXY

    # catchup and incident settings
    catchup_max_gap_minutes: int = 60

    _static_folder_path: str = "opennem/static/"

    # API Keys

    # APVI
    apvi_token: str | None = None

    # willy weather client
    willyweather_api_key: str | None = None

    # cloudflare
    cloudflare_account_id: str | None = None
    cloudflare_api_key: str | None = None

    # twitter — main account (@OpenNem, weekly summaries, general posts)
    twitter_api_key: str | None = None
    twitter_api_key_secret: str | None = None
    twitter_access_token: str | None = None
    twitter_access_token_secret: str | None = None

    # twitter — records account (milestone/record posts)
    twitter_records_api_key: str | None = None
    twitter_records_api_key_secret: str | None = None
    twitter_records_access_token: str | None = None
    twitter_records_access_token_secret: str | None = None

    # bluesky — main account (weekly summaries, general posts)
    bluesky_handle: str | None = None
    bluesky_password: str | None = None

    # bluesky — records account (milestone/record posts)
    bluesky_records_handle: str | None = None
    bluesky_records_password: str | None = None

    # feature flags
    run_milestones: bool = True  # do we enable the milestones
    # debounce interval-period milestone NOTIFICATIONS (e.g. battery charging) so a ramping
    # value doesn't fire a Slack/social notification every interval on the way up/down. The
    # record itself is always persisted — dropping it decimated the stored chain (#651) — only
    # the announcement is suppressed when the record lands fewer than this many intervals after
    # the previous record in its chain. 0 disables. Day+ periods are spaced far enough apart to
    # never trip this. See opennem.recordreactor.utils.should_notify_milestone
    milestone_interval_debounce_intervals: int = 10
    # rooftop solar lands 30 minutes to two hours after the interval it covers, so an interval
    # checked as soon as the grid data arrives is partial for every series containing solar
    # (#652). Those series - network/region totals, solar, renewables, renewable proportion - stop
    # at the last settled interval, derived from the data (the latest interval with rooftop rows
    # for every region) and falling back to this many minutes behind the last completed interval
    # when that can't be determined. Series with no rooftop in them (coal, gas, wind, batteries,
    # fossils, demand, price) are not held back at all. The same window is re-scanned each run so
    # intervals aren't skipped when rooftop lands in a 30-minute block. Day+ periods are not gated
    # on this. See opennem.recordreactor.metric_registry.row_contains_rooftop
    milestone_interval_settle_lag_minutes: int = 60
    # the interval window starts from the last settled interval the incremental checker actually
    # covered (kept in the crawl_meta watermark), not just a settle lag before the current one, so
    # a settled interval that jumps further than the lag between runs doesn't skip intervals
    # (#662). This bounds how far back that catch-up may reach; anything older is the gap
    # backfill's job. See opennem.recordreactor.incremental.get_interval_window_start
    milestone_interval_max_catchup_hours: int = 24
    # how long the incremental milestone checker may go without completing a pass before its
    # missed window is handed to a backlog job. measured against a durable watermark of the last
    # completed pass, not against the newest record — a healthy system goes days without setting
    # one (#658). 3h rather than the old 24h: an outage longer than
    # milestone_interval_settle_lag_minutes already loses interval records that the next pass
    # can't recover, so repairing same-day is the point, and the job is single-flight, out of band
    # and cooled down. ordinary restarts take seconds and never reach this.
    # See opennem.recordreactor.incremental._enqueue_gap_backfill_if_needed
    milestone_gap_backfill_threshold_hours: int = 3
    run_crawlers: bool = True  # do we enable the crawlers
    redirect_api_static: bool = True  # redirect api endpoints to statics where applicable
    show_emissions_in_power_outputs: bool = True  # show emissions in power outputs
    show_emission_factors_in_power_outputs: bool = True  # show emissions in power outputs
    flows_v4: bool = True  # v4 flow solver — always on, no feature flag needed
    # clerk API key
    clerk_secret_key: str | None = None
    api_jwks_url: str = "https://clerk.dev/.well-known/jwks.json"

    # unkey.dev
    unkey_root_key: str | None = None
    unkey_api_id: str | None = None

    # openai
    openai_api_key: str | None = None

    # mailgun
    mailgun_api_key: str | None = None

    # sanity cms setup
    sanity_project_id: str | None = None
    sanity_dataset_id: str | None = None
    sanity_api_key: str | None = None

    # if the worker should run or fallback to maintenance mode
    run_worker: bool = True

    # pylint: disable=no-self-argument
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, log_value: str) -> str | None:
        _log_value = log_value.upper().strip()

        if _log_value not in SUPPORTED_LOG_LEVEL_NAMES:
            raise SettingsException(f"Invalid log level: {_log_value}")

        return _log_value

    @property
    def static_folder_path(self) -> str:
        static_path: Path = Path(self._static_folder_path)

        if not static_path.is_dir():
            raise SettingsException(f"{static_path} is not a folder")

        return str(static_path.resolve())

    @property
    def debug(self) -> bool:
        return self.env.lower() in ("local", "dev", "development", "staging")

    @property
    def is_prod(self) -> bool:
        return self.env.lower() in ("production", "prod")

    @property
    def is_dev(self) -> bool:
        return self.env.lower() in ("local", "dev", "development", "staging")

    @property
    def is_local(self) -> bool:
        return self.env.lower() in ("local")
