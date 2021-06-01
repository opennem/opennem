from datetime import datetime

from opennem.schema.core import BaseConfig


class AEMOFileDownloadSection(BaseConfig):
    published_date: datetime
    filename: str
    download_url: str
    file_size: float
    source_url: str
    source_title: str
