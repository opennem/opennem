from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, PostgresDsn, RedisDsn
from pydantic.class_validators import validator
from scrapy.settings import Settings
from scrapy.utils.project import get_project_settings

SUPPORTED_LOG_LEVEL_NAMES = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class OpennemSettings(BaseSettings):
    env: str = "development"

    log_level: str = "DEBUG"

    db_url: PostgresDsn = "postgres://opennem:opennem@127.0.0.1:15433/opennem"

    cache_url: RedisDsn = "redis://127.0.0.1"

    sentry_url: Optional[str]

    prometheus_url: Optional[str]

    scrapyd_url: str = "http://scrapyd:6800"

    scrapyd_project_name: str = "opennem"

    google_places_api_key: Optional[str] = None

    requests_cache_path: str = ".requests"

    slack_hook_url: Optional[str]

    export_local: bool = False

    s3_bucket_path: str = "s3://data.opennem.org.au/"

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

    # timeout on http requests
    # see opennem.utils.http
    http_timeout: int = 30

    # number of retries by default
    http_retries: int = 5

    # cache http requests locally
    http_cache_local: bool = False

    _static_folder_path: str = "opennem/static/"

    # @todo overwrite scrapy settings here
    scrapy: Optional[Settings] = get_project_settings()

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

    class Config:
        fields = {
            "env": {"env": "ENV"},
            "log_level": {"env": "LOG_LEVEL"},
            "_static_folder_path": {"env": "STATIC_PATH"},
            "export_local": {"env": "EXPORT_LOCAL"},
            "db_url": {"env": "DATABASE_HOST_URL"},
            "cache_url": {"env": "REDIS_HOST_URL"},
            "sentry_url": {"env": "SENTRY_URL"},
            "scrapyd_url": {"env": "SCRAPYD_URL"},
            "prometheus_url": {"env": "PROMETHEUS_URL"},
            "slack_hook_url": {"env": "MONITORING_SLACK_HOOK"},
            "s3_bucket_path": {"env": "S3_DATA_BUCKET_PATH"},
            "server_port": {"env": "PORT"},
            "server_host": {"env": "HOST"},
            "cache_scada_values_ttl_sec": {"env": "CACHE_SCADA_TTL"},
            "db_debug": {"env": "DB_DEBUG"},
            "http_cache_local": {"env": "HTTP_CACHE_LOCAL"},
        }
