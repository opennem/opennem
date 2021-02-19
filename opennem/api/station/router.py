from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from opennem.core.dispatch_type import DispatchType
from opennem.db import get_database_engine, get_database_session
from opennem.db.models.opennem import Facility, FuelTech, Location, Revision, Station
from opennem.schema.opennem import StationSchema

from .schema import StationIDList, StationModification, StationRecord, StationUpdateResponse

router = APIRouter()


@router.get(
    "/",
    response_model=List[StationRecord],
    description="Get a list of all stations",
    response_model_exclude_none=True,
)
def stations(
    session: Session = Depends(get_database_session),
    facilities_include: Optional[bool] = Query(False, description="Include facilities in records"),
    revisions_include: Optional[bool] = Query(False, description="Include revisions in records"),
    history_include: Optional[bool] = Query(False, description="Include history in records"),
    only_approved: Optional[bool] = Query(
        False, description="Only show approved stations not those pending"
    ),
    name: Optional[str] = None,
    limit: Optional[int] = None,
    page: int = 1,
) -> List[StationSchema]:
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
        stations = stations.outerjoin(Facility, Facility.station_id == Station.id).outerjoin(
            FuelTech, Facility.fueltech_id == FuelTech.code
        )

    if revisions_include:
        stations = stations.outerjoin(Revision, Revision.station_id == Station.id)

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


@router.get(
    "/",
    name="station lookup",
    description="""Lookup station by code or network_code. \
        Require one of code or network_code""",
    response_model=List[StationRecord],
    response_model_exclude_none=True,
)
def station_lookup(
    session: Session = Depends(get_database_session),
    station_code: Optional[str] = Query(None, description="Code of the station to lookup"),
    network_code: Optional[str] = Query(None, description="The network code to lookup"),
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


@router.get(
    "/ids",
    response_model=List[StationIDList],
    description="Get a list of station ids for dropdowns",
    response_model_exclude_none=True,
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

    stations = stations.order_by(
        Station.id,
    )

    stations = stations.all()

    return stations


@router.get(
    "/{station_code:path}",
    response_model=StationSchema,
    description="Get a single station by code",
    response_model_exclude_none=True,
)
def station(
    session: Session = Depends(get_database_session),
    engine=Depends(get_database_engine),
    station_code: str = None,
    only_generators: bool = Query(True, description="Show only generators"),
    power_include: Optional[bool] = Query(False, description="Include last week of power output"),
    revisions_include: Optional[bool] = Query(False, description="Include revisions in records"),
    history_include: Optional[bool] = Query(False, description="Include history in records"),
) -> StationSchema:

    station = (
        session.query(Station)
        .filter(Station.code == station_code)
        .filter(Facility.station_id == Station.id)
        .filter(~Facility.code.endswith("NL1"))
    )

    if only_generators:
        station = station.filter(Facility.dispatch_type == DispatchType.GENERATOR)

    station = station.one_or_none()

    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")

    if not station.facilities:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station has no facilities",
        )

    station.network = station.facilities[0].network_id

    if revisions_include:
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
                    lambda rev: rev.schema == "facility" and rev.code == facility.code,
                    revisions,
                )
            )

    if power_include:
        pass

    if station.location and station.location.geom:
        __query = """
            select
                code,
                ST_Distance(l.geom, bs.geom, false) / 1000.0 as dist
            from bom_station bs, location l
            where
                l.id = {id}
                and bs.priority < 2
            order by dist
            limit 1
        """.format(
            id=station.location.id
        )

        result = []

        with engine.connect() as c:
            result = list(c.execute(__query))

            if len(result):
                station.location.weather_nearest = {
                    "code": result[0][0],
                    "distance": round(result[0][1], 2),
                }

    return station


@router.get(
    "/history",
    name="station all history",
    description="""Get history for all stations""",
    response_model=List[StationSchema],
)
def stations_history(session: Session = Depends(get_database_session)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get(
    "/station/history/{station_code}",
    name="station history",
    description="""Get history for a station""",
    response_model=StationSchema,
)
def station_history(station_code: str, session: Session = Depends(get_database_session)):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post(
    "/",
    name="station",
    # response_model=StationSchema,
    description="Create a station",
)
def station_create(
    session: Session = Depends(get_database_session),
    # station: StationSubmission = None,
):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.put("/{station_id}", name="Station update")
def station_update(
    station_id: int,
    data: StationModification = {},
    session: Session = Depends(get_database_session),
) -> dict:
    station = session.query(Station).get(station_id)

    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")

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

    response = StationUpdateResponse(success=True, record=station)

    return response
