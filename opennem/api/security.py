""" API security  """
import logging

from authlib.jose import JsonWebKey, JsonWebToken, JWTClaims, KeySet, errors
from cachetools import TTLCache, cached
from fastapi import Depends, HTTPException, security, status
from fastapi.security import OAuth2PasswordBearer

from opennem import settings
from opennem.clients.unkey import unkey_validate
from opennem.utils.http import http

logger = logging.getLogger("pagecog.api.security")

token_scheme = security.HTTPBearer()

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


@cached(TTLCache(maxsize=1, ttl=3600))
def get_jwks() -> KeySet:
    """
    Get cached or new JWKS from clerk.dev.
    """
    logger.info("Fetching JWKS from %s", settings.api_jwks_url)
    with http.get(settings.api_jwks_url) as response:
        response.raise_for_status()
        return JsonWebKey.import_key_set(response.json())


def decode_token(
    token: security.HTTPAuthorizationCredentials = Depends(token_scheme),
    jwks: KeySet = Depends(get_jwks),
) -> JWTClaims:
    """
    Validate & decode JWT.
    """
    try:
        claims = JsonWebToken(["RS256"]).decode(
            s=token.credentials,
            key=jwks,
            claims_options={
                # Example of validating audience to match expected value
                "aud": {"essential": True, "values": ["domaingenius"]}
            },
        )

        claims.validate()
    except errors.JoseError as e:
        logger.exception("Unable to decode token")
        raise HTTPException(status_code=403, detail="Bad auth token") from e

    return claims


async def get_current_user(token: str = Depends(decode_token)) -> str:
    try:
        pass
    except Exception as e:
        logger.error(e)
        raise credentials_exception from e
    user = token
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user=Depends(get_current_user)) -> str:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# unkey validation

# security bearer API key token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def api_key_auth(api_key: str = Depends(oauth2_scheme)) -> None:
    user_api_key = unkey_validate(api_key=api_key)
    if not user_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")
