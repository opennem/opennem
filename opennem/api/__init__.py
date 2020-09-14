from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import Field
from sqlalchemy.orm import Session, sessionmaker
from starlette import status

from opennem.controllers.stations import get_stations
from opennem.core.loader import load_data
from opennem.db import db_connect, get_database_session
from opennem.db.models.opennem import (
    Facility,
    FuelTech,
    Location,
    Network,
    Revision,
    Station,
)
from opennem.importer.registry import registry_import
from opennem.schema.opennem import (
    FueltechSchema,
    NetworkSchema,
    RevisionSchema,
    StationSchema,
    StationSubmission,
)

from .schema import (
    FueltechResponse,
    RevisionModification,
    StationResponse,
    UpdateResponse,
)

app = FastAPI(title="OpenNEM", debug=True, version="3.0.0-alpha")

origins = [
    "https://admin.opennem.org.au",
    "https://admin.opennem.test",
    "http://localhost",
    "http://localhost:3000",
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
    response_model=List[StationSchema],
    description="Get a list of all stations",
)
def stations(
    session: Session = Depends(get_database_session),
    revisions_include: Optional[bool] = Query(
        False, description="Include revisions in records"
    ),
    history_include: Optional[bool] = Query(
        False, description="Include history in records"
    ),
    only_approved: Optional[bool] = Query(
        False, description="Include history in records"
    ),
    name: Optional[str] = None,
    limit: Optional[int] = None,
    page: int = 1,
) -> List[StationSchema]:
    stations = (
        session.query(Station)
        .join(Station.location)
        .outerjoin(Facility, Facility.station_id == Station.id)
        .outerjoin(FuelTech, Facility.fueltech_id == FuelTech.code)
        # .group_by(Station.code)
        # .filter(Facility.fueltech_id.isnot(None))
        # .filter(Facility.status_id.isnot(None))
    )

    if revisions_include:
        stations = stations.outerjoin(
            Revision, Revision.station_id == Station.id
        )

    if only_approved:
        stations = stations.filter(Station.approved == True)

    if name:
        stations = stations.filter(Station.name.like("%{}%".format(name)))

    stations = stations.order_by(
        Facility.network_region,
        Station.name,
        Facility.network_code,
        Facility.code,
    )

    stations = stations.all()

    if not revisions_include:
        return stations

    # stations = [StationSchema.from_orm(i) for i in stations]

    # revisions = [
    # RevisionSchema.parse_obj(i) for i in session.query(Revision).all()
    # ]

    # revisions = session.query(Revision).all()

    # for station in stations:
    #     _revisions = list(
    #         filter(
    #             lambda rev: rev.schema == "station"
    #             and rev.code == station.code,
    #             revisions,
    #         )
    #     )
    #     # station.revisions = _revisions

    #     station.revision_ids = [i.id for i in _revisions]

    #     for facility in station.facilities:
    #         _revisions = list(
    #             filter(
    #                 lambda rev: rev.schema == "facility"
    #                 and rev.code == facility.code,
    #                 revisions,
    #             )
    #         )

    #         # facility.revisions = _revisions
    #         facility.revision_ids = [i.id for i in _revisions]

    return stations


@app.get(
    "/station/{station_code}",
    response_model=StationSchema,
    description="Get a single station by code",
)
def station(
    session: Session = Depends(get_database_session),
    station_code: str = None,
    revisions_include: Optional[bool] = False,
    history_include: Optional[bool] = False,
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


# @app.get(
#     "/station",
#     name="station lookup",
#     description="""Lookup station by code or network_code. \
#         Require one of code or network_code""",
#     response_model=List[StationSchema],
# )
# def station_update(
#     session: Session = Depends(get_database_session),
#     station_code: Optional[str] = None,
#     network_code: Optional[str] = None,
# ) -> List[StationSchema]:
#     if not station_code and not network_code:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

#     station = session.query(Station)

#     if station_code:
#         station = station.filter_by(code=station_code)

#     if network_code:
#         station = station.filter_by(network_name=network_code)

#     stations = station.all()

#     if not stations:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

#     return stations


@app.post(
    "/stations",
    name="station",
    # response_model=StationSchema,
    description="Create a station",
)
def station_create(
    session: Session = Depends(get_database_session),
    station: StationSubmission = None,
):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@app.get("/facilities", name="facilities")
def facilities(session: Session = Depends(get_database_session)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


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


@app.put("/revision/{revision_id}", name="revision update")
def revision_update(
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
