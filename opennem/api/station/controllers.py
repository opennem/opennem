from sqlalchemy.orm.session import Session

from opennem.db.models.opennem import Facility, Station


def get_stations(
    session: Session,
    only_approved: bool = True,
    name: str | None = None,
    limit: int | None = None,
    page: int = 1,
) -> list[Station]:
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
        stations = stations.filter(Station.name.like(f"%{name}%"))

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
