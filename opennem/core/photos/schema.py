from typing import Optional

from opennem.schema.core import BaseConfig


class PhotoImportSchema(BaseConfig):
    """Defines a schema for photo imports"""

    network_id: str
    station_code: str
    is_primary: bool
    image_url: str

    author: Optional[str]
    author_link: Optional[str]
    license: Optional[str]
    license_link: Optional[str]
