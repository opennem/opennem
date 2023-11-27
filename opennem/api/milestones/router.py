from fastapi import APIRouter
from fastapi_versioning import version

from opennem.recordreactor.schema import MilestoneRecord

from .queries import get_milestones

domain_router = APIRouter(tags=["Milestones"], include_in_schema=False)


@domain_router.get("/")
@version(4)
async def api_get_domains(limit: int = 100) -> list[MilestoneRecord]:
    """Get a list of milestones"""
    db_records = await get_milestones(limit=limit)

    milestone_records = [MilestoneRecord(**i) for i in db_records]

    return milestone_records
