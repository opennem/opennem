from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from opennem.db import get_database_session
from opennem.db.models.opennem import Facility

from .schema import (
    FacilityModification,
    FacilityModificationTypes,
    FacilityRecord,
    FacilityUpdateResponse,
)

router = APIRouter()


@router.get(
    "/",
    name="Facilities",
    description="Get facilities",
    response_model=List[FacilityRecord],
)
def facilities(
    session: Session = Depends(get_database_session),
) -> FacilityRecord:
    facilities = session.query(Facility).all()

    return facilities


@router.get(
    "/{facility_code:path}", name="Facility", response_model=FacilityRecord,
)
def facility(
    facility_code: str = Query(str, description="Facility code"),
    session: Session = Depends(get_database_session),
) -> FacilityRecord:
    facility = (
        session.query(Facility).filter_by(code=facility_code).one_or_none()
    )

    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found"
        )

    return facility


@router.put("/{facility_id}", name="Facility update")
def facility_update(
    facility_id: int,
    data: FacilityModification = {},
    session: Session = Depends(get_database_session),
) -> dict:
    facility = session.query(Facility).get(facility_id)

    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found"
        )

    if data.modification == FacilityModificationTypes.approve:

        if facility.approved is True:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Facility already approved",
            )

        facility.approved = True
        facility.approved_at = datetime.now()
        facility.approved_by = "opennem.admin"

    if data.modification == FacilityModificationTypes.reject:
        facility.approved = False

    session.add(facility)
    session.commit()

    response = FacilityUpdateResponse(success=True, record=facility)

    return response
