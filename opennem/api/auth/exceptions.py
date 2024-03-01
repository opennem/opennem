"""
OpenNEM Auth Exceptions

"""

from opennem.api.exceptions import OpennemBaseHttpException


class UnauthorizedRequest(OpennemBaseHttpException):
    """Base 401 return for unauthorized"""

    detail = "Unauthorized request"
    status_code = 401


class BadCredentials(OpennemBaseHttpException):
    """Base 403 return for permission denied"""

    detail = "Bad credentials"
    status_code = 403


class BadCredentialsKeyNotFound(BadCredentials):
    """API Key not found exception"""

    detail = "Bad credentials: Key not found"


class RevokedCredentials(OpennemBaseHttpException):
    """401 for revoked credentials"""

    detail = "Credentials revoked or expires"
    status_code = 401
