"""Admin router: pure Clerk-admin routes mounted at /v4/admin.

Every route here is hidden from the OpenAPI schema (router + include_router both set
include_in_schema=False) and requires a real Clerk admin API key. The dev/internal bypass keys are rejected.
"""

from fastapi import APIRouter, Depends

from opennem.api.admin.social import router as social_router
from opennem.api.security import get_admin_user

admin_router = APIRouter(include_in_schema=False, dependencies=[Depends(get_admin_user)])

admin_router.include_router(social_router, prefix="/social", tags=["Social"], include_in_schema=False)
