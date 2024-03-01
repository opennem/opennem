"""
OpenNEM String Validators

Used in Pydantic schemas
"""

from opennem.core.normalizers import string_is_urlsafe


def urlsafe_str_validator(v: str) -> str:
    """Validate that a string is url safe. Assumes already passed through string validation"""

    if not isinstance(v, str):
        raise ValueError()

    if string_is_urlsafe(v):
        return v

    raise ValueError()
