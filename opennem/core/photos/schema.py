from opennem.schema.core import BaseConfig


class PhotoImportSchema(BaseConfig):
    """Defines a schema for photo imports"""

    network_id: str
    station_code: str
    is_primary: bool
    image_url: str

    author: str | None
    author_link: str | None
    license: str | None
    license_link: str | None
