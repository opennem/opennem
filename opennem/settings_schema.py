"""
OpenNEM Settings Schema

Everything that can be changed is set here and can be overwritten with ENV settings
"""

from datetime import UTC
from datetime import timezone as pytimezone
from pathlib import Path

from pydantic import AliasChoices, AnyUrl, Field, RedisDsn, field_validator
from pydantic_settings import BaseSettings

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

    redis_url: RedisDsn = Field(
        "redis://127.0.0.1",
        validation_alias=AliasChoices("REDIS_HOST_URL", "cache_url"),
    )

    clickhouse_url: AnyUrl = Field(
        "http://127.0.0.1:8123/opennem",
        description="Clickhouse URL",
    )

    # if we're doing a dry run
    dry_run: bool = False

    sentry_url: str | None = None

    # This is the module where crawlers are found
    crawlers_module: str = "opennem.crawlers"

    requests_cache_path: str = ".requests"

    # Slack notifications
    slack_hook_new_facilities: str | None = None
    slack_hook_monitoring: str | None = None
    slack_hook_feedback: str | None = None
    slack_admin_alert: list[str] | None = ["nik"]

    # APVI
    apvi_token: str | None = None

    export_local: bool = False

    s3_bucket_path: str = Field("data.opennem.org.au", validation_alias=AliasChoices("S3_DATA_BUCKET_PATH"))

    # opennem output settings
    interval_default: str = "15m"
    period_default: str = "7d"
    precision_default: int = 4

    # show database debug
    db_debug: bool = False

    # cache scada values for
    cache_scada_values_ttl_sec: int = 60 * 5

    # asgi server settings
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_reload: bool = False
    server_ssl: bool = False

    # timeout on http requests
    # see opennem.utils.http
    http_timeout: int = 20

    # number of retries by default
    http_retries: int = 5

    # cache http requests locally
    http_cache_local: bool = False
    http_verify_ssl: bool = True
    https_proxy_url: str | None = None  # @note don't let it confict with env HTTP_PROXY

    _static_folder_path: str = "opennem/static/"

    # output schema options
    # output values for region, network etc. in lower case
    schema_output_lowercase_strings: bool = True
    # prepend the country code in the id
    schema_output_id_country: bool = False

    # templates folder relative to opennem module root
    templates_dir: str = "templates"

    # api key cookie settings
    api_app_auth_name: str = "onau"
    api_user_auth_name: str = "onuu"
    api_app_auth_key_length: int = 24
    api_auth_cookie_domain: str = "opennem.org.au"

    # API Keys

    # willy weather client
    willyweather_api_key: str | None = None

    # cloudflare
    cloudflare_account_id: str | None = None
    cloudflare_api_key: str | None = None

    tmp_file_prefix: str | None = "opennem_"

    # alert threshold level in minutes for interval delay monitoring
    monitor_interval_alert_threshold: int | None = 10

    # feature flags
    run_crawlers: bool = True  # do we enable the crawlers
    flows_and_emissions_v3: bool = True  #
    redirect_api_static: bool = True  # redirect api endpoints to statics where applicable
    show_emissions_in_power_outputs: bool = True  # show emissions in power outputs
    show_emission_factors_in_power_outputs: bool = True  # show emissions in power outputs
    compact_number_ouput_in_json: bool = False  # compact number output in json

    # send daily fueltech summary
    send_daily_fueltech_summary: bool = True

    # profiler options
    profiler_level: str = "NOISY"

    # clerk API key
    clerk_secret_key: str | None = None
    api_jwks_url: str = "https://clerk.dev/.well-known/jwks.json"

    # unkey.dev
    unkey_root_key: str | None = None
    unkey_api_id: str | None = None

    # openai
    openai_api_key: str | None = None

    # api messages
    api_messages: list[str] = [
        "OpenNEM API will be moving behind a login soon. Please see the discssion at https://github.com/opennem/opennem/discussions/243"
    ]

    # percentage of old API requests to return deprecation messages
    api_deprecation_proportion: int = 0

    # API Dev key
    api_dev_key: str | None = None

    # webhooks
    webhook_secret: str | None = None

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
