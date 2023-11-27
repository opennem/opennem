from fastapi import APIRouter
from fastapi_versioning import version

from opennem.recordreactor.schema import MilestoneRecord

from .queries import get_milestones

milestones_router = APIRouter(tags=["Milestones"], include_in_schema=True)


@milestones_router.get("/")
@version(4)
def api_get_domains(limit: int = 100, page_number: int = 1) -> list[MilestoneRecord]:
    """Get a list of milestones"""
    db_records = get_milestones(limit=limit, page_number=page_number)

    milestone_records = [MilestoneRecord(**i) for i in db_records]

    return milestone_records
