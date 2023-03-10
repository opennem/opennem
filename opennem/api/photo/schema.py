from opennem.api.schema import ApiBase


class Photo(ApiBase):
    hash_id: str
    width: int
    height: int
    photo_url: str | None

    license_type: str | None
    license_link: str | None
    author: str | None
    author_link: str | None

    is_primary: bool | None
    order: int | None
