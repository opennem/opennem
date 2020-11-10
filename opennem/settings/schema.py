from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, PostgresDsn, RedisDsn
from scrapy.settings import Settings
from scrapy.utils.project import get_project_settings


class OpennemSettings(BaseSettings):
    env: str = "development"
    db_url: PostgresDsn = "postgresql://opennem:opennem@127.0.0.1:15433/opennem"
    cache_url: RedisDsn = "redis://127.0.0.1"
    sentry_url: Optional[str]

    google_places_api_key: Optional[str] = None

    requests_cache_path: str = ".requests"

    slack_hook_url: Optional[str]

    export_local: bool = False

    s3_bucket_path: str = "s3://data.opennem.org.au/"

    interval_default: str = "15m"

    period_default: str = "7d"

    precision_default: int = 4

    _static_folder_path: str = "opennem/static/"

    # @todo overwrite scrapy settings here
    scrapy: Optional[Settings] = get_project_settings()

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
            "_static_folder_path": {"env": "STATIC_PATH"},
            "export_local": {"env": "EXPORT_LOCAL"},
            "db_url": {"env": "DATABASE_HOST_URL"},
            "cache_url": {"env": "REDIS_HOST_URL"},
            "sentry_url": {"env": "SENTRY_URL"},
            "slack_hook_url": {"env": "WATCHDOG_SLACK_HOOK"},
            "s3_bucket_path": {"env": "S3_DATA_BUCKET_PATH"},
        }
