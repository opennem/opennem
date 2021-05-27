"""
OpenNEM Auth Utils

"""
import secrets

API_KEY_LENGTH = 16


def generate_api_key(key_length: int = API_KEY_LENGTH) -> str:
    """Generates an URL-safe API key using the secrets library and settings"""
    return secrets.token_urlsafe(API_KEY_LENGTH)
