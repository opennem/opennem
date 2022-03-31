"""
OpenNEM Settings Schema

Everything that can be changed is set here and can be overwritten with ENV settings
"""
from datetime import timezone as pytimezone
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Union

from pydantic import BaseSettings
from pydantic.class_validators import validator

from opennem.schema.types import PostgresSqlAlchemyDsn

if TYPE_CHECKING:
    RedisDsn = str
else:
    from pydantic import RedisDsn

SUPPORTED_LOG_LEVEL_NAMES = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class OpennemSettings(BaseSettings):
    env: str = "development"

    log_level: str = "DEBUG"

    timezone: pytimezone = pytimezone.utc

    # Set maintenance mode - workers won't run and API will return a MaintenanceMode response
    maintenance_mode: bool = False

    # @NOTE pydantic settings assignment type mismatch from mypy
    # https://github.com/samuelcolvin/pydantic/issues/1490
    db_url: Optional[PostgresSqlAlchemyDsn]  # type: ignore

    cache_url: RedisDsn = "redis://127.0.0.1"

    sentry_url: Optional[str]

    prometheus_url: Optional[str]

    # This is the module where crawlers are found
    crawlers_module: str = "opennem.crawlers"

    google_places_api_key: Optional[str] = None

    requests_cache_path: str = ".requests"

    # Slack notifications
    slack_notifications: bool = False

    slack_hook_url: Optional[str]

    # twilio setup
    twilio_sid: Optional[str]
    twilio_auth_token: Optional[str]
    twilio_from_number: Optional[str]

    # APVI
    apvi_token: Optional[str]

    export_local: bool = False

    s3_bucket_path: str = "s3://data.opennem.org.au/"

    photos_bucket_path: str = "s3://photos.opennem.org.au/"

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
    monitoring_alert_sms: Optional[str] = None
    monitoring_alert_slack_user: Optional[List[str]] = None

    # api key cookie settings
    api_app_auth_name: str = "onau"
    api_user_auth_name: str = "onuu"
    api_app_auth_key_length: int = 24
    api_auth_cookie_domain: str = "opennem.org.au"

    # trello key / secret for feedback endpoint
    trello_api_key: Optional[str]
    trello_api_secret: Optional[str]

    # feedback
    # this is the feedback board
    feedback_trello_board_id: str = "60a48f32c97cf221e3d4bec1"

    # willy weather client
    willyweather_api_key: Optional[str]

    # pylint: disable=no-self-argument
    @validator("log_level")
    def validate_log_level(cls, log_value: str) -> Optional[str]:

        _log_value = log_value.upper().strip()

        if _log_value not in SUPPORTED_LOG_LEVEL_NAMES:
            raise Exception("Invalid log level: {}".format(_log_value))

        return _log_value

    @property
    def sentry_enabled(self) -> bool:
        return self.sentry_url is not None

    @property
    def static_folder_path(self) -> str:
        _path: Path = Path(self._static_folder_path)

        if not _path.is_dir():
            raise Exception("{} is not a folder".format(_path))

        return str(_path.resolve())

    @property
    def debug(self) -> bool:
        if self.env in ["development", "staging"]:
            return True
        return False

    @property
    def is_prod(self) -> bool:
        return self.env == "production" or self.env == "prod"

    class Config:
        fields = {
            "env": {"env": "ENV"},
            "log_level": {"env": "LOG_LEVEL"},
            "_static_folder_path": {"env": "STATIC_PATH"},
            "db_url": {"env": "DATABASE_HOST_URL"},
            "cache_url": {"env": "REDIS_HOST_URL"},
            "slack_notifications": {"env": "SLACK_NOTIFICATIONS"},
            "slack_hook_url": {"env": "MONITORING_SLACK_HOOK"},
            "s3_bucket_path": {"env": "S3_DATA_BUCKET_PATH"},
            "server_port": {"env": "PORT"},
            "server_host": {"env": "HOST"},
            "cache_scada_values_ttl_sec": {"env": "CACHE_SCADA_TTL"},
        }
