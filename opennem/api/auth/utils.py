"""
OpenNEM Auth Utils

"""
import secrets

API_KEY_LENGTH = 16


def generate_api_key(key_length: int = API_KEY_LENGTH) -> str:
    """Generates an URL-safe API key using the secrets library and settings"""
    return secrets.token_urlsafe(API_KEY_LENGTH)


def cookie_name_from_auth_name(auth_name: str) -> str:
    """Takes an auth name and returns what the name of the cookie will be.
    At the moment we are just prepending _"""

    cookie_auth_name = auth_name

    if not cookie_auth_name.startswith("_"):
        cookie_auth_name = f"_{auth_name.lower()}"

    return cookie_auth_name
