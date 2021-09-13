from typing import Any

from fastapi import HTTPException
from starlette import status
from starlette.responses import Response

from opennem.schema.opennem import OpennemErrorSchema


class OpennemBaseHttpException(HTTPException):
    """Base OpenNEM Exception"""

    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, status_code: int = 404):
        if not self.status_code:
            self.status_code = status_code


class ItemNotFound(OpennemBaseHttpException):
    status_code = status.HTTP_404_NOT_FOUND


class InvalidDateRange(OpennemBaseHttpException):
    status_code = status.HTTP_404_NOT_FOUND


class MaintenanceMode(OpennemBaseHttpException):
    status_code = status.HTTP_204_NO_CONTENT
    detail = "Maintenance Mode"


class OpenNEMInvalidNetwork(OpennemBaseHttpException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Invalid Network"


class OpenNEMInvalidNetworkRegion(OpennemBaseHttpException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Invalid Network Region"


class OpenNEMNoResults(OpennemBaseHttpException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "No Results"


class OpennemExceptionResponse(Response):
    media_type = "application/json"
    response_class: OpennemErrorSchema

    def __init__(
        self,
        response_class: OpennemErrorSchema,
        status_code: int = 200,
        headers: dict = None,
    ):
        self.response_class = response_class
        self.status_code = status_code

        super().__init__(content=b"", status_code=status_code, headers=headers)

    def render(self, content: Any) -> bytes:
        return self.response_class.json().encode("utf-8")  # type: ignore
