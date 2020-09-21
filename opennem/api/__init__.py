from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette import status

from opennem.api.stats import router as stats_router
from opennem.db import get_database_session
from opennem.db.models.opennem import (
    Facility,
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
    StationIDList,
    StationModification,
    StationResponse,
    UpdateResponse,
)

app = FastAPI(title="OpenNEM", debug=True, version="3.0.0-alpha.3")

app.include_router(stats_router, tags=["Stats"], prefix="/stats")


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
    "/stations",
    # response_model=List[StationSchema],
    description="Get a list of all stations",
)
def stations(
    session: Session = Depends(get_database_session),
    facilities_include: Optional[bool] = Query(
        False, description="Include facilities in records"
    ),
    revisions_include: Optional[bool] = Query(
        False, description="Include revisions in records"
    ),
    history_include: Optional[bool] = Query(
        False, description="Include history in records"
    ),
    only_approved: Optional[bool] = Query(
        False, description="Only show approved stations not those pending"
    ),
    name: Optional[str] = None,
    limit: Optional[int] = None,
    page: int = 1,
):
    stations = (
        session.query(Station)
        .join(Location)
        .enable_eagerloads(True)
        #
        # .group_by(Station.code)
        # .filter(Facility.fueltech_id.isnot(None))
        # .filter(Facility.status_id.isnot(None))
    )

    if facilities_include:
        stations = stations.outerjoin(
            Facility, Facility.station_id == Station.id
        ).outerjoin(FuelTech, Facility.fueltech_id == FuelTech.code)

    if revisions_include:
        stations = stations.outerjoin(
            Revision, Revision.station_id == Station.id
        )

    if only_approved:
        stations = stations.filter(Station.approved == True)

    if name:
        stations = stations.filter(Station.name.like("%{}%".format(name)))

    stations = stations.order_by(
        # Facility.network_region,
        Station.name,
        # Facility.network_code,
        # Facility.code,
    )

    stations = stations.all()

    return stations


@app.get(
    "/station/ids",
    response_model=List[StationIDList],
    description="Get a list of station ids for dropdowns",
)
def station_ids(
    session: Session = Depends(get_database_session),
    only_approved: Optional[bool] = Query(
        True, description="Only show approved stations not those pending"
    ),
) -> List[StationIDList]:
    stations = session.query(Station).join(Station.location)

    if only_approved:
        stations = stations.filter(Station.approved == True)

    stations = stations.order_by(Station.id,)

    stations = stations.all()

    return stations


@app.get(
    "/station/{station_code}",
    response_model=StationSchema,
    description="Get a single station by code",
)
def station(
    session: Session = Depends(get_database_session),
    station_code: str = None,
    revisions_include: Optional[bool] = Query(
        False, description="Include revisions in records"
    ),
    history_include: Optional[bool] = Query(
        False, description="Include history in records"
    ),
):
    station = (
        session.query(Station)
        .filter(Station.code == station_code)
        .one_or_none()
    )

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Station not found"
        )

    if not revisions_include:
        return station

    revisions = session.query(Revision).all()

    station.revisions = list(
        filter(
            lambda rev: rev.schema == "station" and rev.code == station.code,
            revisions,
        )
    )

    for facility in station.facilities:
        facility.revisions = list(
            filter(
                lambda rev: rev.schema == "facility"
                and rev.code == facility.code,
                revisions,
            )
        )


@app.get(
    "/station/history",
    name="station all history",
    description="""Get history for all stations""",
    response_model=List[StationSchema],
)
def stations_history(session: Session = Depends(get_database_session)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@app.get(
    "/station/history/{station_code}",
    name="station history",
    description="""Get history for a station""",
    response_model=StationSchema,
)
def station_history(
    station_code: str, session: Session = Depends(get_database_session)
):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@app.get(
    "/station",
    name="station lookup",
    description="""Lookup station by code or network_code. \
        Require one of code or network_code""",
    response_model=List[StationSchema],
)
def station_lookup(
    session: Session = Depends(get_database_session),
    station_code: Optional[str] = Query(
        None, description="Code of the station to lookup"
    ),
    network_code: Optional[str] = Query(
        None, description="The network code to lookup"
    ),
) -> List[StationSchema]:
    if not station_code and not network_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    station = session.query(Station)

    if station_code:
        station = station.filter_by(code=station_code)

    if network_code:
        station = station.filter_by(network_name=network_code)

    stations = station.all()

    if not stations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return stations


@app.post(
    "/stations",
    name="station",
    # response_model=StationSchema,
    description="Create a station",
)
def station_create(
    session: Session = Depends(get_database_session),
    # station: StationSubmission = None,
):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@app.get(
    "/facilities",
    name="facilities",
    description="Get facilities",
    response_model=List[FacilitySchema],
)
def facilities(session: Session = Depends(get_database_session)):
    facilities = session.query(Facility).all()

    return facilities


@app.get("/facility/{facility_code}")
def facility(
    session: Session = Depends(get_database_session), station_code: str = None
):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


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


@app.put("/station/{station_id}", name="Station update")
def station_update(
    station_id: int,
    data: StationModification = {},
    session: Session = Depends(get_database_session),
) -> dict:
    station = session.query(Station).get(station_id)

    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Station not found"
        )

    if data.modification == "approve":

        if station.approved is True:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Station already approved",
            )

        station.approved = True
        station.approved_at = datetime.now()
        station.approved_by = "opennem.admin"

    if data.modification == "reject":
        station.approved = False

    session.add(station)
    session.commit()

    response = UpdateResponse(success=True, record=station)

    return response


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
