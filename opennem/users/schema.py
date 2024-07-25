from enum import Enum

from pydantic import BaseModel


class OpenNEMRoles(Enum):
    admin = "admin"
    user = "user"
    anonymous = "anonymous"


class OpenNEMUserRateLimit(BaseModel):
    limit: int
    remaining: int
    reset: int


class OpenNEMUser(BaseModel):
    valid: bool
    id: str
    owner_id: str | None = None
    meta: dict | None = None
    error: str | None = None
    rate_limit: OpenNEMUserRateLimit | None = None
    roles: list[OpenNEMRoles] = [OpenNEMRoles.anonymous]
