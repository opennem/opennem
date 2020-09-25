from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette import status

from opennem.api.locations import router as locations_router
from opennem.api.station.router import router as station_router
from opennem.api.stats.router import router as stats_router
from opennem.core.dispatch_type import DispatchType
from opennem.core.time import human_to_interval
from opennem.db import get_database_session
from opennem.db.models.opennem import (
    Facility,
    FacilityScada,
    FuelTech,
    Location,
    Network,
    Revision,
    Station,
)
from opennem.schema.opennem import (
    FacilitySchema,
    FueltechSchema,
    NetworkSchema,
    RevisionSchema,
    StationSchema,
)

from .schema import (
    FueltechResponse,
    RevisionModification,
    RevisionModificationResponse,
)

app = FastAPI(title="OpenNEM", debug=True, version="3.0.0-alpha.3")

app.include_router(stats_router, tags=["Stats"], prefix="/stats")
app.include_router(locations_router, tags=["Locations"], prefix="/locations")
app.include_router(station_router, tags=["Stations"], prefix="/station")


origins = [
    "https://dev.opennem.org.au",
    "https://admin.opennem.org.au",
    "https://admin.opennem.test",
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/facilities",
    name="facilities",
    description="Get facilities",
    response_model=List[FacilitySchema],
)
def facilities(session: Session = Depends(get_database_session)):
    facilities = session.query(Facility).all()

    return facilities


@app.get(
    "/facility/{facility_code:path}",
    name="Facility",
    response_model=FacilitySchema,
)
def facility(
    facility_code: str = Query(str, description="Facility code"),
    session: Session = Depends(get_database_session),
) -> FacilitySchema:
    facility = (
        session.query(Facility).filter_by(code=facility_code).one_or_none()
    )

    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found"
        )

    return facility


@app.get("/revisions")
def revisions(
    session: Session = Depends(get_database_session),
) -> List[Revision]:
    revisions = session.query(Revision).all()

    return revisions


@app.get("/revision/{revision_id}")
def revision(
    revision_id: int, session: Session = Depends(get_database_session)
):
    revision = session.query(Revision).get(revision_id)

    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found"
        )

    return revision


@app.put("/facility/{facility_id}", name="Facility update")
def facility_update(
    facility_id: int,
    data: StationModification = {},
    session: Session = Depends(get_database_session),
) -> dict:
    facility = session.query(Facility).get(facility_id)

    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Facility not found"
        )

    if data.modification == "approve":

        if facility.approved is True:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Facility already approved",
            )

        facility.approved = True
        facility.approved_at = datetime.now()
        facility.approved_by = "opennem.admin"

    if data.modification == "reject":
        facility.approved = False

    session.add(facility)
    session.commit()

    response = UpdateResponse(success=True, record=facility)

    return response


REVISION_TARGET_MAP = {
    "station": Station,
    "facility": Facility,
    "location": Location,
}


@app.put("/revision/{revision_id}", name="revision update")
def revision_update(
    data: RevisionModification = {},
    session: Session = Depends(get_database_session),
    revision_id: int = None,
) -> dict:
    revision: Revision = session.query(Revision).get(revision_id)

    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found"
        )

    if data.modification == "reject":
        revision.discarded = True
        revision.approved = False
        revision.discarded_by = "opennem.admin"
        revision.discarded_at = datetime.now()

        session.add(revision)
        session.commit()

        response = UpdateResponse(success=True, record=revision)

    revision.approved = True
    revision.approved_at = datetime.now()
    revision.approved_by = "opennem.admin"

    if revision.parent_type not in REVISION_TARGET_MAP.keys():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Revision schema type not supported",
        )

    revision_target_type = REVISION_TARGET_MAP[revision.parent_type]

    revision_target = session.query(revision_target_type).get(
        revision.parent_id
    )

    if not revision_target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revision target record not found",
        )

    for target_field, target_value in revision.changes.items():
        if hasattr(revision_target, f"{target_field}_code"):
            target_field = "{}_code".format(target_field)

        if hasattr(revision_target, f"{target_field}_id"):
            target_field = "{}_id".format(target_field)

        if not hasattr(revision_target, target_field):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid revision field",
            )

        try:
            setattr(revision_target, target_field, target_value)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error setting revision",
            )

    session.add(revision_target)
    session.add(revision)
    session.commit()

    response = RevisionModificationResponse(
        success=True, record=revision, target=revision_target
    )

    return response


@app.post("/revision/approve/{revision_id}", name="revision approve")
def revision_approve(
    data: RevisionModification = {},
    session: Session = Depends(get_database_session),
    revision_id: int = None,
) -> dict:
    revision = session.query(Revision).get(revision_id)

    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found"
        )

    revision.approved = True
    revision.approved_by = "opennem.admin"

    session.add(revision)
    session.commit()

    response = UpdateResponse(success=True, record=revision)

    return response


@app.post("/revision/reject/{revision_id}", name="revision reject")
def revision_reject(
    data: RevisionModification = {},
    session: Session = Depends(get_database_session),
    revision_id: int = None,
) -> dict:
    revision: Revision = session.query(Revision).get(revision_id)

    if not revision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found"
        )

    revision.approved = False
    revision.discarded = False
    revision.discarded_by = "opennem.admin"
    revision.discarded_at = datetime.now()

    session.add(revision)
    session.commit()

    response = UpdateResponse(success=True, record=revision)

    return response


@app.get("/networks", response_model=List[NetworkSchema])
def networks(
    session: Session = Depends(get_database_session),
) -> List[NetworkSchema]:
    networks = session.query(Network).all()

    if not networks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    response = [NetworkSchema.parse_obj(i) for i in networks]

    return response


@app.get("/fueltechs", response_model=List[FueltechSchema])
def fueltechs(
    session: Session = Depends(get_database_session),
) -> FueltechResponse:
    fueltechs = session.query(FuelTech).all()

    if not fueltechs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    response = [FueltechSchema.parse_obj(i) for i in fueltechs]

    return response
