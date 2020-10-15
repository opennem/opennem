import decimal
from typing import List, Optional

from sqlalchemy.orm.session import Session

from opennem.db.models.opennem import Facility, Location, Station


def get_stations(
    session: Session,
    only_approved: bool = True,
    name: Optional[str] = None,
    limit: Optional[int] = None,
    page: int = 1,
) -> List[Station]:
    """
        API controller that gets all stations sorted and joined

    """

    stations = (
        session.query(Station)
        .join(Station.facilities)
        .join(Station.location)
        .join(Facility.fueltech)
        .filter(Facility.fueltech_id.isnot(None))
        .filter(Facility.status_id.isnot(None))
    )

    if name:
        stations = stations.filter(Station.name.like("%{}%".format(name)))

    if only_approved:
        stations = stations.filter(Station.approved.is_(True))

    stations = stations.order_by(
        Facility.network_region,
        Station.name,
        Facility.network_code,
        Facility.code,
    )

    if limit:
        stations = stations.limit(limit)

    stations = stations.all()

    return stations
