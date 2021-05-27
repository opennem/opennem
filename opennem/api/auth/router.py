"""
OpenNEM API Auth Router


"""

from typing import Dict

from fastapi import APIRouter, Depends
from fastapi.security.api_key import APIKey

from opennem.api.auth.key import get_api_key
from opennem.api.auth.schema import AuthApiKeyInfoResponse

router = APIRouter()


@router.get("/logout")
def auth_logout() -> Dict:

    _response = {"status": "OK"}

    return _response


@router.get("/info", response_model=AuthApiKeyInfoResponse)
def app_auth_test(api_record: APIKey = Depends(get_api_key)) -> AuthApiKeyInfoResponse:
    _response = AuthApiKeyInfoResponse(record=api_record)

    return _response
