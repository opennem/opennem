from typing import Any

from fastapi import HTTPException
from starlette import status
from starlette.responses import Response


class OpennemBaseHttpException(HTTPException):
    """ Base OpenNEM Exception """

    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, status_code: int = 404):
        if not self.status_code:
            self.status_code = status_code

class InvalidDateRange(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
