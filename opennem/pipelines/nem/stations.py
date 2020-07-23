import json
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.sql import text

from opennem.core.facilitystations import facility_station_join_by_name
from opennem.core.facilitystatus import map_v3_states
from opennem.core.fueltechs import lookup_fueltech
from opennem.core.normalizers import (
    clean_capacity,
    name_normalizer,
    normalize_duid,
    normalize_string,
    participant_name_filter,
    station_name_cleaner,
)
from opennem.db.models.opennem import (
    FacilityStatus,
    NemFacility,
    NemParticipant,
    NemStation,
)
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class NemMMSSingle(DatabaseStoreBase):
    """

    """

    def get_table(self, item):
        if not "tables" in item:
            logger.error(item)
            raise Exception("No tables passed to pipeline")

        table_names = [i["name"] for i in item["tables"]]

        if not self.table in table_names:
            logger.debug(
                "Skipping {} pipeline step as table {} not processed".format(
                    self.__class__, self.table
                )
            )
            return False

        table = [
            i
            for i in item["tables"]
            if "name" in i and i["name"] == self.table
        ]

        return table.pop() if len(table) else None


class NemStoreMMSStations(NemMMSSingle):
    """

    """

    table = "PARTICIPANT_REGISTRATION_STATION"

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        table = self.get_table(item)

        if not table:
            return item

        records_updated = 0
        records_created = 0

        records = table["records"]
        for record in records:
            created = False

            duid = normalize_duid(record["STATIONID"])
            name = name_normalizer(record["STATIONNAME"])
            name_clean = station_name_cleaner(record["STATIONNAME"])
            network_name = normalize_string(record["STATIONNAME"])
            address1 = normalize_string(record["ADDRESS1"])
            address2 = normalize_string(record["ADDRESS2"])
            city = normalize_string(record["CITY"])
            state = normalize_string(record["STATE"])
            postcode = normalize_string(record["POSTCODE"])

            station = (
                s.query(NemStation)
                .filter(NemStation.code == duid)
                .one_or_none()
            )

            if not station:
                station = NemStation(code=duid,)

                records_created += 1
                created = True
            else:
                records_updated += 1

            station.name = name
            station.name_clean = name_clean
            station.network_name = network_name
            station.address1 = address1
            station.address2 = address2
            station.locality = city
            station.state = state

            try:
                s.add(station)
                s.commit()
            except Exception as e:
                logger.error(e)

            logger.debug(
                "{} station record with id {}".format(
                    "Created" if created else "Updated", duid
                )
            )

        logger.info(
            "Created {} records and updated {}".format(
                records_created, records_updated
            )
        )


class NemStoreMMSStationStatus(NemMMSSingle):
    """

    """

    table = "PARTICIPANT_REGISTRATION_STATIONOPERATINGSTATUS"

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        table = self.get_table(item)

        if not table:
            return item

        records = table["records"]
        for record in records:
            duid = normalize_duid(record["STATIONID"])
            # authorized_date = name_normalizer(record["AUTHORISEDDATE"])
            status = map_v3_states(record["STATUS"])

            station = (
                s.query(NemStation)
                .filter(NemStation.code == duid)
                .one_or_none()
            )

            if not station:
                logger.error("Could not find station {}".format(duid))
                continue

            station.status = status

            try:
                s.add(station)
                s.commit()
            except Exception as e:
                logger.error(e)
