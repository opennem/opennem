from fastapi import APIRouter, HTTPException
from fastapi_versioning import version
from starlette import status

from opennem.recordreactor.schema import MilestoneRecord

from .queries import get_milestones

domain_router = APIRouter(tags=["Milestones"], include_in_schema=False)


@domain_router.get("/")
@version(4)
async def api_get_domains() -> list[MilestoneRecord]:
    """Get a list of milestones"""
    db_records = await get_milestones()

    milestone_records = [MilestoneRecord(**i) for i in db_records]

    return milestone_records


@domain_router.get("/{domain_name}")
async def api_get_domain(domain_name: str) -> dict:
    """Get a list of domains"""
    result = await get_milestones(domain_name=domain_name)

    if not result:
        raise HTTPException(detail="Domain not found", code=status.HTTP_404_NOT_FOUND)

    return result[0]
