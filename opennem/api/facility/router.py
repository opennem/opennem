from fastapi import APIRouter, Depends, HTTPException
from fastapi_versionizer import api_version
from sqlalchemy.orm import Session
from starlette import status

from opennem.db import get_scoped_session
from opennem.db.models.opennem import Facility

from .schema import FacilityRecord

router = APIRouter()


@api_version(3)
@router.get(
    "/",
    name="Facilities",
    description="Get facilities",
    response_model=list[FacilityRecord],
)
def facilities(
    session: Session = Depends(get_scoped_session),
) -> list[FacilityRecord]:
    facilities = session.query(Facility).all()

    return facilities


@api_version(3)
@router.get(
    "/{facility_code:path}",
    name="Facility",
    response_model=FacilityRecord,
)
def facility(
    facility_code: str,
    session: Session = Depends(get_scoped_session),
) -> FacilityRecord:
    facility = session.query(Facility).filter_by(code=facility_code).one_or_none()

    if not facility:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found")

    return facility
