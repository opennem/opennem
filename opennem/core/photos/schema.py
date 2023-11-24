from opennem.schema.core import BaseConfig


class PhotoImportSchema(BaseConfig):
    """Defines a schema for photo imports"""

    network_id: str
    station_code: str
    is_primary: bool
    image_url: str

    author: str | None = None
    author_link: str | None = None
    license: str | None = None
    license_link: str | None = None
