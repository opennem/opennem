"""
OpenNEM Settings Schema

Everything that can be changed is set here and can be overwritten with ENV settings
"""
from datetime import timezone as pytimezone
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseSettings
from pydantic.class_validators import validator

from opennem.schema.types import PostgresSqlAlchemyDsn

if TYPE_CHECKING:
    RedisDsn = str
else:
    from pydantic import RedisDsn

SUPPORTED_LOG_LEVEL_NAMES = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class SettingsException(Exception):
    pass


class OpennemSettings(BaseSettings):
    env: str = "development"

    log_level: str = "DEBUG"

    timezone: pytimezone | str = pytimezone.utc

    # Set maintenance mode - workers won't run and API will return a MaintenanceMode response
    maintenance_mode: bool = False

    # @NOTE pydantic settings assignment type mismatch from mypy
    # https://github.com/samuelcolvin/pydantic/issues/1490
    db_url: PostgresSqlAlchemyDsn = "postgresql://user:pass@127.0.0.1:15444/opennem"  # type: ignore

    cache_url: RedisDsn = "redis://127.0.0.1"

    sentry_url: str | None

    prometheus_url: str | None

    # This is the module where crawlers are found
    crawlers_module: str = "opennem.crawlers"

    google_places_api_key: str | None = None

    requests_cache_path: str = ".requests"

    # Slack notifications
    slack_notifications: bool = False

    slack_hook_url: str | None

    # twilio setup
    twilio_sid: str | None
    twilio_auth_token: str | None
    twilio_from_number: str | None

    # APVI
    apvi_token: str | None

    export_local: bool = False

    s3_bucket_path: str = "s3://data.opennem.org.au/"
    backup_bucket_path: str = "backups.opennem.org.au"
    photos_bucket_path: str = "s3://photos.opennem.org.au/"

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

    # used in testing to not run database queries
    dry_run: bool = False

    _static_folder_path: str = "opennem/static/"

    # output schema options
    # output values for region, network etc. in lower case
    schema_output_lowercase_strings: bool = True
    # prepend the country code in the id
    schema_output_id_country: bool = False

    # db views used

    # energy view used
    db_energy_view: str = "mv_facility_all"
    db_energy_view_recent: str = "mv_facility_45d"

    # workers
    workers_run: bool = True
    workers_db_run: bool = True

    # templates folder relative to opennem module root
    templates_dir: str = "templates"

    # monitoring
    monitoring_alert_sms: str | None = None
    monitoring_alert_slack_user: Optional[List[str]] = None

    # api key cookie settings
    api_app_auth_name: str = "onau"
    api_user_auth_name: str = "onuu"
    api_app_auth_key_length: int = 24
    api_auth_cookie_domain: str = "opennem.org.au"

    # trello key / secret for feedback endpoint
    trello_api_key: str | None
    trello_api_secret: str | None

    # feedback
    # this is the feedback board
    feedback_trello_board_id: str = "60a48f32c97cf221e3d4bec1"

    # willy weather client
    willyweather_api_key: str | None

    # cloudflare
    cloudflare_account_id: str | None
    cloudflare_api_key: str | None

    tmp_file_prefix: str | None = "opennem_"

    slack_admin_alert: list[str] | None = ["nik"]

    # alert threshold level in minutes for interval delay monitoring
    monitor_interval_alert_threshold: int | None = 10

    # feature flags
    flows_and_emissions_v2: bool = False

    # pylint: disable=no-self-argument
    @validator("log_level")
    def validate_log_level(cls, log_value: str) -> str | None:

        _log_value = log_value.upper().strip()

        if _log_value not in SUPPORTED_LOG_LEVEL_NAMES:
            raise SettingsException(f"Invalid log level: {_log_value}")

        return _log_value

    @property
    def sentry_enabled(self) -> bool:
        return self.sentry_url is not None

    @property
    def static_folder_path(self) -> str:
        static_path: Path = Path(self._static_folder_path)

        if not static_path.is_dir():
            raise SettingsException(f"{static_path} is not a folder")

        return str(static_path.resolve())

    @property
    def debug(self) -> bool:
        return self.env in ("development", "staging")

    @property
    def is_prod(self) -> bool:
        return self.env in ("production", "prod")

    class Config:
        fields = {
            "env": {"env": "ENV"},
            "log_level": {"env": "LOG_LEVEL"},
            "_static_folder_path": {"env": "STATIC_PATH"},
            "db_url": {"env": "DATABASE_HOST_URL"},
            "cache_url": {"env": "REDIS_HOST_URL"},
            "slack_hook_url": {"env": "MONITORING_SLACK_HOOK"},
            "s3_bucket_path": {"env": "S3_DATA_BUCKET_PATH"},
            "server_port": {"env": "PORT"},
            "server_host": {"env": "HOST"},
            "cache_scada_values_ttl_sec": {"env": "CACHE_SCADA_TTL"},
        }
