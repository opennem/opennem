"""
OpenNEM Auth Exceptions

"""
from opennem.api.exceptions import OpennemBaseHttpException


class BadCredentials(OpennemBaseHttpException):
    """Base 403 return for permission denied"""

    detail = "Bad credentials"
    status_code = 403


class BadCredentialsKeyNotFound(BadCredentials):
    """API Key not found exception"""

    detail = "Bad credentials: key not found"
