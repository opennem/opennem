from fastapi import HTTPException
from starlette import status


class ItemNotFound(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND


class InvalidDateRange(HTTPException):
    status_code = status.HTTP_404_NOT_FOUND
