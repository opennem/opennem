"""
OpenNEM String Validators

Used in Pydantic schemas
"""

from pydantic.errors import PydanticTypeError, StrError

from opennem.core.normalizers import string_is_urlsafe


class UrlsafeStrError(PydanticTypeError):
    msg_template = "url safe str type expected"


def urlsafe_str_validator(v: str) -> str:
    """Validate that a string is url safe. Assumes already passed through string validation"""

    if not isinstance(v, str):
        raise StrError()

    if string_is_urlsafe(v):
        return v

    raise UrlsafeStrError()
