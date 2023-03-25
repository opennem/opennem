import logging

from fastapi import Security
from fastapi.security.api_key import APIKeyCookie, APIKeyHeader, APIKeyQuery

from opennem import settings
from opennem.core.validators.security import validate_api_key
from opennem.db import get_scoped_session
from opennem.db.models.opennem import ApiKeys

from .exceptions import BadCredentials, BadCredentialsKeyNotFound, RevokedCredentials, UnauthorizedRequest
from .schema import AuthApiKeyRecord
from .utils import cookie_name_from_auth_name, header_name_from_auth_name

logger = logging.getLogger("opennem.auth")

APP_AUTH_COOKIE_NAME = cookie_name_from_auth_name(settings.api_app_auth_name)
APP_AUTH_HEADER_NAME = header_name_from_auth_name(settings.api_app_auth_name)

api_key_query = APIKeyQuery(name=APP_AUTH_COOKIE_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=APP_AUTH_HEADER_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=APP_AUTH_COOKIE_NAME, auto_error=False)


def get_api_key_record(api_key: str) -> AuthApiKeyRecord:
    """Get an API Key record from the database"""
    session = get_scoped_session()

    try:
        api_key = validate_api_key(api_key)
    except Exception as e:
        logger.error(f"Bad API key {api_key}: {e}")
        raise UnauthorizedRequest()

    api_key_record: ApiKeys | None = session.query(ApiKeys).filter_by(keyid=api_key).one_or_none()

    if not api_key_record:
        logger.error(f"API key not found: {api_key}")
        raise BadCredentialsKeyNotFound()

    if api_key_record.revoked:
        logger.error(f"API key revoked: {api_key}")
        raise RevokedCredentials()

    api_key_schema = AuthApiKeyRecord.from_orm(api_key_record)

    return api_key_schema


async def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
    api_key_cookie: str = Security(api_key_cookie),
) -> AuthApiKeyRecord:
    """Validate the api key passed from"""

    if api_key_query and (f := get_api_key_record(api_key_query)):
        return f

    if api_key_header and (f := get_api_key_record(api_key_header)):
        return f

    if api_key_cookie and (f := get_api_key_record(api_key_cookie)):
        return f

    raise BadCredentials()
