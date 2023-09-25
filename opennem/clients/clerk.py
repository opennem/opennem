""" clerk.dev client """

import logging
from typing import Any

from httpx import HTTPError, Response
from pydantic import BaseModel

from opennem import settings
from opennem.utils.httpx import httpx_factory

logger = logging.getLogger("opennem.clients.clerk")

# Basic Models


class ClerkResponseError(BaseModel):
    message: str
    long_message: str
    code: str
    meta: Any | None = None


class ClerkNewUser(BaseModel):
    first_name: str
    last_name: str | None = None
    email_address: list[str]
    skip_password_checks: bool = False
    skip_password_requirement: bool = False
    password: str | None = None
    external_id: str | None = None


# Exceptions
class ClerkClientException(Exception):
    pass


class NoActiveSessionException(Exception):
    def __init__(self, client_id: str):
        super().__init__(f"no active sessions for given client {client_id}")


# Main client
class ClerkClient:
    api_endpoint = "https://api.clerk.dev/v1/"

    def __init__(self) -> None:
        self.session = httpx_factory(base_url=self.api_endpoint)

        # Set headers for session requests
        headers = {"Accept": "application/json", "Authorization": f"Bearer {settings.clerk_api_key}"}

        self.session.headers.update(headers)

    def fix_and_validate_endpoint(self, endpoint: str) -> str:
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        return endpoint

    async def __aenter__(self) -> type[Any]:  # sometimes we cheat
        return self

    async def __aexit__(self, *excinfo) -> None:  # type:ignore
        await self.session.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> Response:  # type: ignore
        try:
            res = await self.session.request(method=method, url=path, **kwargs)
            res.raise_for_status()
        except HTTPError as e:
            raise ClerkClientException(f"{res.status_code}: {e}") from e

        return res

    async def get(self, path: str, params: dict | None = None, **kwargs: dict) -> Response:
        return await self._request("get", path, params=params, **kwargs)

    async def post(self, path: str, data: dict | BaseModel | None = None, **kwargs: dict) -> Response:
        if isinstance(data, BaseModel):
            try:
                data = data.model_dump(exclude_unset=True)  # type: ignore
            except ValueError:
                pass

            if data and not isinstance(data, dict):
                data = dict(data)

            logger.info(data)

        return await self._request("post", path, json=data, **kwargs)

    async def put(self, path: str, data: dict | BaseModel | None = None, **kwargs: dict) -> Response:
        if isinstance(data, BaseModel):
            data = data.dict(exclude_unset=True)

        return await self._request("put", path, json=data, **kwargs)

    # User Methods
    async def users_get(self) -> list[dict]:
        """Get all users"""
        res = await self.get("users")
        return res.json()

    async def user_create(self, user: ClerkNewUser) -> dict:
        """Create a new user"""
        res = await self.post("users", data=user)
        return res.json()


if __name__ == "__main__":
    import asyncio
    from pprint import pprint

    # clerk = ClerkClient()
    # users = asyncio.run(clerk.get_users())
    async def test_list_users() -> None:
        async with ClerkClient() as clerk:
            await clerk.users_get()
            users = await clerk.users_get()

        return users

    async def test_create_user() -> None:
        user = ClerkNewUser(
            first_name="Test",
            last_name="User",
            email_address=["tes2t@test.com"],
            skip_password_checks=True,
            skip_password_requirement=True,
        )

        async with ClerkClient() as clerk:
            await clerk.user_create(user)

    # user = asyncio.get_event_loop().run_until_complete(test_create_user())

    # pprint(user)

    users = asyncio.get_event_loop().run_until_complete(test_list_users())

    for user in users:
        print("----------------")
        pprint(user)
