"""
OpenNEM API Auth Router


"""

from fastapi import APIRouter, Depends

from opennem.api.auth.key import get_api_key
from opennem.api.auth.schema import AuthApiKeyInfoResponse, AuthApiKeyRecord

router = APIRouter()


@router.get("/logout")
def auth_logout() -> dict:
    _response = {"status": "OK"}

    return _response


@router.get("/info", response_model=AuthApiKeyInfoResponse)
def app_auth_test(api_record: AuthApiKeyRecord = Depends(get_api_key)) -> AuthApiKeyInfoResponse:
    _response = AuthApiKeyInfoResponse(record=api_record, total_records=1)

    return _response
