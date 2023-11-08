"""
OpenNEM Auth Utils

"""
import secrets

from fastapi import HTTPException

from opennem import settings
from opennem.utils.security import random_percentage


def generate_api_key(key_length: int = settings.api_app_auth_key_length) -> str:
    """Generates an URL-safe API key using the secrets library and settings"""
    return secrets.token_urlsafe(64)[:key_length]


def cookie_name_from_auth_name(auth_name: str) -> str:
    """Takes an auth name and returns what the name of the cookie will be.
    At the moment we are just prepending _"""

    cookie_auth_name = auth_name

    if not cookie_auth_name.startswith("_"):
        cookie_auth_name = f"_{auth_name.lower()}"

    return cookie_auth_name


def header_name_from_auth_name(auth_name: str) -> str:
    """Takes an auth name and returns what the http header name will be"""

    header_auth_name = f"X-{auth_name.upper()}"

    return header_auth_name


def opennem_api_return_deprecation_message() -> HTTPException | None:
    """Returns a 410 Gone response with a deprecation message"""
    if random_percentage(settings.api_deprecation_proportion):
        return HTTPException(
            status_code=410,
            detail="This endpoint is deprecatedPlease use the new API.",
        )
    return None
