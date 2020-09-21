from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from opennem.db import get_database_session
from opennem.db.models.opennem import FacilityScada

router = APIRouter()


@router.get("/power", name="stats:power")
def stats_power(session: Session = Depends(get_database_session),):
    stats = session.query(FacilityScada).all()

    return stats
