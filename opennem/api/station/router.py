from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette import status

from opennem.core.dispatch_type import DispatchType
from opennem.db import get_database_session
from opennem.db.models.opennem import Facility, FuelTech, Location, Network, Revision, Station
from opennem.schema.opennem import StationSchema

from .schema import StationIDList, StationRecord

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
    "/{country_code}/{network_id}/{station_code:path}",
    response_model=StationSchema,
    description="Get a single station by code",
    response_model_exclude_none=True,
)
def station(
    country_code: str,
    network_id: str,
    station_code: str,
    session: Session = Depends(get_database_session),
    only_generators: bool = Query(True, description="Show only generators"),
) -> StationSchema:

    station = (
        session.query(Station)
        .filter(Station.code == station_code)
        .filter(Facility.station_id == Station.id)
        .filter(~Facility.code.endswith("NL1"))
        .filter(Facility.network_id == network_id)
        .filter(Network.country == country_code)
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

    return station
