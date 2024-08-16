"""
Create stations on NEM for interconnectors
which provide stats on region flows.


"""

import logging

from opennem.core.dispatch_type import DispatchType
from opennem.core.loader import load_data
from opennem.core.networks import state_from_network_region
from opennem.core.parsers.aemo.mms import AEMOParserException, parse_aemo_mms_csv
from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility, Location, Station
from opennem.schema.aemo.mms import MarketConfigInterconnector
from opennem.utils.mime import decode_bytes

logger = logging.getLogger("opennem.importer.interconnectors")

# INTERCONNECTOR_TABLE = "market_config_interconnector"  # full name with namespace
INTERCONNECTOR_TABLE = "interconnector"


def import_nem_interconnects() -> None:
    session = SessionLocal()

    # Load the MMS CSV file that contains interconnector info
    csv_data = load_data(
        "mms/PUBLIC_DVD_INTERCONNECTOR_202006010000.CSV",
        from_project=True,
    )

    # gotta be a string otherwise decode
    if not isinstance(csv_data, str):
        csv_data = decode_bytes(csv_data)

    # parse the AEMO CSV into schemas
    aemo_table_set = None

    try:
        aemo_table_set = parse_aemo_mms_csv(csv_data)
    except AEMOParserException as e:
        logger.error(e)
        return None

    if not aemo_table_set:
        return None

    if not aemo_table_set.has_table(INTERCONNECTOR_TABLE):
        logger.error(f"Could not find table {INTERCONNECTOR_TABLE}")
        logger.info("Have tables: {}".format(", ".join([i.name for i in aemo_table_set.tables])))
        return None

    int_table = aemo_table_set.get_table(INTERCONNECTOR_TABLE)

    if not int_table:
        logger.error(f"Could not fetch table: {INTERCONNECTOR_TABLE}")

    if not int_table.records:
        logger.error(f"Could not fetch records for table: {INTERCONNECTOR_TABLE}")

    records: list[MarketConfigInterconnector] = int_table.records

    for interconnector in records:
        if not isinstance(interconnector, MarketConfigInterconnector):
            if isinstance(interconnector, dict) and "interconnectorid" in interconnector:
                interconnector = MarketConfigInterconnector(**interconnector)
                # raise Exception("Not what we're looking for ")

        # skip SNOWY
        # @TODO do these need to be remapped for historical
        if interconnector.regionfrom == "SNOWY1" or interconnector.regionto == "SNOWY1":
            continue

        logger.debug(interconnector)

        if interconnector.interconnectorid.endswith("-2"):
            logger.info(f"Skipping old interconnector {interconnector.interconnectorid}")
            continue

        interconnector_station = (
            session.query(Station)
            .filter_by(code=interconnector.interconnectorid)
            # .filter_by(network_code="NEM")
            .one_or_none()
        )

        if interconnector_station:
            logging.debug(f"Found existing interconnector station: {interconnector_station.code}")
        else:
            logging.debug(f"Creating new interconnector station: {interconnector.interconnectorid}")

            interconnector_station = Station(
                code=interconnector.interconnectorid,
                network_code="NEM",
            )

        # leave this as false so that they don't appear in geojson / facilities page
        interconnector_station.approved = False

        interconnector_station.created_by = "opennem.importer.interconnectors"

        if not interconnector_station.location:
            interconnector_station.location = Location(state=state_from_network_region(interconnector.regionfrom))

        interconnector_station.name = interconnector.description

        # for network_region in [interconnector.regionfrom, interconnector.regionto]:
        # Fac1
        int_facility = (
            session.query(Facility)
            .filter_by(code=interconnector.interconnectorid)
            .filter_by(dispatch_type=DispatchType.GENERATOR)
            .filter_by(network_id="NEM")
            .filter_by(network_region=interconnector.regionfrom)
            .one_or_none()
        )

        if not int_facility:
            int_facility = Facility(  # type: ignore
                code=interconnector.interconnectorid,
                network_code=interconnector.interconnectorid,
                dispatch_type=DispatchType.GENERATOR,
                network_id="NEM",
                network_region=interconnector.regionfrom,
            )

        int_facility.status_id = "operating"
        int_facility.approved = False
        int_facility.created_by = "opennem.importer.interconnectors"
        int_facility.fueltech_id = None

        int_facility.interconnector = True
        int_facility.network_code = interconnector.interconnectorid
        int_facility.interconnector_region_to = interconnector.regionto
        int_facility.interconnector_region_from = interconnector.regionfrom

        interconnector_station.facilities.append(int_facility)

        try:
            session.add(interconnector_station)
            session.commit()
            logger.info(f"Created interconnector station: {interconnector_station.code}")
        except Exception as e:
            logger.error(f"Could not commit interconnector stations: {e}")

    return None


if __name__ == "__main__":
    import_nem_interconnects()
