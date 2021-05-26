"""
OpenNEM Security Validators

Functions to validate security fields and schemas
"""


def validate_api_key(api_key: str) -> str:
    """Validate an API key"""
    if not isinstance(api_key, str):
        raise ValueError("Invalid API key: wrong type")

    if len(api_key) < 10:
        raise ValueError("API Key too short")

    if len(api_key) > 32:
        raise ValueError("API Key too long")

    return api_key
