from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility, Location, Station

ROOFTOP_CODE = "ROOFTOP"

STATE_NETWORK_REGION_MAP = [
    {"state": "NSW", "network": "NEM", "network_region": "NSW1"},
    {"state": "QLD", "network": "NEM", "network_region": "QLD1"},
    {"state": "VIC", "network": "NEM", "network_region": "VIC1"},
    {"state": "TAS", "network": "NEM", "network_region": "TAS1"},
    {"state": "SA", "network": "NEM", "network_region": "SA1"},
    {"state": "NT", "network": "NEM", "network_region": "NT1"},
    {"state": "WA", "network": "WEM", "network_region": "WEM"},
]


def rooftop_facilities():

    session = SessionLocal()

    for state_map in STATE_NETWORK_REGION_MAP:
        state_rooftop_code = "{}_{}".format(
            ROOFTOP_CODE, state_map["state"].upper()
        )

        rooftop_station = (
            session.query(Station).filter_by(code=ROOFTOP_CODE).one_or_none()
        )

        if not rooftop_station:
            rooftop_station = Station(code=state_rooftop_code,)

        rooftop_station.name = "Rooftop Solar {}".format(state_map["state"])
        rooftop_station.description = "Solar rooftop facilities for {}".format(
            state_map["state"]
        )
        rooftop_station.approved = True
        rooftop_station.approved_by = "opennem.importer.apvi"
        rooftop_station.created_by = "opennem.importer.apvi"

        if not rooftop_station.location:
            rooftop_station.location = Location(state=state_map["state"])

        rooftop_fac = (
            session.query(Facility)
            .filter_by(code=state_rooftop_code)
            .one_or_none()
        )

        if not rooftop_fac:
            rooftop_fac = Facility(code=state_rooftop_code)

        rooftop_fac.network_id = state_map["network"]
        rooftop_fac.network_region = state_map["network_region"]
        rooftop_fac.fueltech_id = "solar_rooftop"
        rooftop_fac.active = True
        rooftop_fac.approved_by = "opennem.importer.apvi"
        rooftop_fac.created_by = "opennem.importer.apvi"

        rooftop_station.facilities.append(rooftop_fac)
        session.add(rooftop_fac)

        session.add(rooftop_station)

    session.commit()


if __name__ == "__main__":
    rooftop_facilities()
