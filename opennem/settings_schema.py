"""
OpenNEM Settings Schema

Everything that can be changed is set here and can be overwritten with ENV settings
"""

from datetime import UTC
from datetime import timezone as pytimezone
from pathlib import Path

from pydantic import AliasChoices, Field, RedisDsn, field_validator
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

    redis_url: RedisDsn = Field(
        RedisDsn("redis://127.0.0.1"),
        validation_alias=AliasChoices("REDIS_HOST_URL", "cache_url"),
    )

    # if we're doing a dry run
    dry_run: bool = False

    sentry_url: str | None = None

    # Slack notifications
    slack_notifications: bool = True
    slack_hook_new_facilities: str | None = None
    slack_hook_monitoring: str | None = None
    slack_hook_feedback: str | None = None
    slack_hook_aemo_market_notices: str | None = None
    slack_admin_alert: list[str] | None = ["nik"]

    # APVI
    apvi_token: str | None = None

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
    http_cache_local: bool = False
    http_verify_ssl: bool = True
    http_proxy_url: str | None = None  # @note don't let it confict with env HTTP_PROXY

    _static_folder_path: str = "opennem/static/"

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

    # feature flags
    run_crawlers: bool = True  # do we enable the crawlers
    redirect_api_static: bool = True  # redirect api endpoints to statics where applicable
    show_emissions_in_power_outputs: bool = True  # show emissions in power outputs
    show_emission_factors_in_power_outputs: bool = True  # show emissions in power outputs

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

    # webhooks
    webhook_secret: str | None = None

    # sanity cms setup
    sanity_project_id: str | None = None
    sanity_dataset_id: str | None = None
    sanity_api_key: str | None = None

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
