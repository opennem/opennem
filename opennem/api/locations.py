from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from opennem.db import get_database_session
from opennem.db.models.opennem import Location
from opennem.schema.opennem import LocationSchema

router = APIRouter()


@router.get("/", description="Locations", response_model=list[LocationSchema])
def locations(
    session: Session = Depends(get_database_session),
) -> list[LocationSchema]:
    locations = session.query(Location).all()

    return locations
