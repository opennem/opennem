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
from opennem.db.models.opennem import Facility, FacilityStatus
from opennem.db.models.opennem import Participant as ParticipantModel
from opennem.db.models.opennem import Station
from opennem.pipelines import DatabaseStoreBase
from opennem.schema.opennem import Participant as ParticipantSchema
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
                s.query(Station).filter(Station.code == duid).one_or_none()
            )

            if not station:
                station = Station(code=duid,)

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
                s.query(Station).filter(Station.code == duid).one_or_none()
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


class NemStoreMMSParticipant(NemMMSSingle):
    """

    """

    table = "PARTICIPANT_REGISTRATION_PARTICIPANT"

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        table = self.get_table(item)

        if not table:
            return item

        records_updated = 0
        records_created = 0

        q = self.engine.execute(text("select code from participant"))

        participant_codes = list(set([i[0] for i in q.fetchall()]))

        records = table["records"]
        for record in records:
            created = False

            participant_schema = ParticipantSchema(
                **{
                    "code": record["PARTICIPANTID"],
                    "name": record["NAME"],
                    "network_name": record["NAME"],
                }
            )

            # pid = normalize_duid(record["PARTICIPANTID"])
            # name = normalize_string(record["NAME"])
            # name_clean = participant_name_filter(record["NAME"])

            participant = (
                s.query(ParticipantModel)
                .filter(ParticipantModel.code == participant_schema.code)
                .one_or_none()
            )

            print(
                "Participant {} found as {} {}".format(
                    record["PARTICIPANTID"],
                    participant,
                    participant_schema.code,
                )
            )

            if not participant:
                participant = ParticipantModel(
                    **{
                        **participant_schema.dict(),
                        "created_by": "au.nem.mms.participant",
                    }
                )

                records_created += 1
                created = True
            else:
                participant.name = participant_schema.name
                participant.network_name = participant_schema.network_name
                records_updated += 1

            try:
                s.add(participant)
                s.commit()
            except Exception as e:
                logger.error(e)

            logger.debug(
                "{} participant record with id {}".format(
                    "Created" if created else "Updated",
                    participant_schema.code,
                )
            )

        logger.info(
            "Created {} records and updated {}".format(
                records_created, records_updated
            )
        )


class NemStoreMMSDudetail(NemMMSSingle):
    """

    """

    table = "PARTICIPANT_REGISTRATION_DUDETAIL"

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

            duid = normalize_duid(record["DUID"])
            capacity_registered = clean_capacity(record["REGISTEREDCAPACITY"])
            capacity_max = clean_capacity(record["MAXCAPACITY"])

            facility = (
                s.query(Facility).filter(Station.code == duid).one_or_none()
            )

            if not facility:
                station = Station(code=duid, created_by="au.nem.mms.dudetail")

                records_created += 1
                created = True
            else:
                records_updated += 1

            facility.capacity_registered = capacity_registered
            facility.capacity_max = capacity_max

            try:
                s.add(station)
                s.commit()
            except Exception as e:
                logger.error(e)

            logger.debug(
                "{} facility record with id {}".format(
                    "Created" if created else "Updated", duid
                )
            )

        logger.info(
            "Created {} facility records and updated {}".format(
                records_created, records_updated
            )
        )


class NemStoreMMSDudetailSummary(NemMMSSingle):
    """

    """

    table = "PARTICIPANT_DUDETAILSUMMARY"

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

            end_date = record["END_DATE"].strip()
            dispatch_type = record["DISPATCHTYPE"].strip()

            if dispatch_type != "DISPATCHTYPE":
                continue

            if end_date != "31/12/2999  12:00:00 am":
                continue

            sid = normalize_duid(record["STATIONID"])
            pid = normalize_duid(record["PARTICIPANTID"])
            capacity_registered = clean_capacity(record["REGISTEREDCAPACITY"])
            capacity_max = clean_capacity(record["MAXCAPACITY"])
            network_region = normalize_string(record["REGIONID"])

            station = (
                s.query(Station).filter(Station.code == sid).one_or_none()
            )

            if not station:
                station = Station(
                    code=sid, created_by="au.nem.mms.dudetail_summary"
                )

                records_created += 1
                created = True
            else:
                records_updated += 1

            facility.capacity_registered = capacity_registered

            try:
                s.add(station)
                s.commit()
            except Exception as e:
                logger.error(e)

            logger.debug(
                "{} facility record with id {}".format(
                    "Created" if created else "Updated", sid
                )
            )

        logger.info(
            "Created {} facility records and updated {}".format(
                records_created, records_updated
            )
        )
