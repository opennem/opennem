import json
import logging
from datetime import datetime
from typing import Optional

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.sql import text

from opennem.core.dispatch_type import DispatchType, parse_dispatch_type
from opennem.core.facilitystations import facility_station_join_by_name
from opennem.core.fueltechs import lookup_fueltech
from opennem.core.normalizers import (
    clean_capacity,
    name_normalizer,
    normalize_aemo_region,
    normalize_duid,
    normalize_string,
    participant_name_filter,
    station_name_cleaner,
)
from opennem.core.station_duid_map import (
    facility_has_station_remap,
    facility_map_station,
)
from opennem.db.models.opennem import Facility, FacilityStatus
from opennem.db.models.opennem import Participant as ParticipantModel
from opennem.db.models.opennem import Station
from opennem.pipelines import DatabaseStoreBase
from opennem.schema.opennem import ParticipantSchema
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class NemMMSSingle(DatabaseStoreBase):
    """

    """

    def get_table(self, item):
        if "tables" not in item:
            logger.error(item)
            raise Exception("No tables passed to pipeline")

        table_names = [i["name"] for i in item["tables"]]

        if self.table not in table_names:
            logger.debug(
                "Skipping %s pipeline step as table %s not processed",
                self.__class__,
                self.table,
            )
            return False

        table = [
            i
            for i in item["tables"]
            if "name" in i and i["name"] == self.table
        ]

        return table.pop() if len(table) else None


class NemStoreMMSStations(DatabaseStoreBase):
    """

    """

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        records_updated = 0
        records_created = 0

        for record in item:
            created = False

            duid = normalize_duid(record["STATIONID"])
            name = station_name_cleaner(record["STATIONNAME"])
            network_name = normalize_string(record["STATIONNAME"])
            address1 = normalize_string(record["ADDRESS1"])
            address2 = normalize_string(record["ADDRESS2"])
            city = normalize_string(record["CITY"])
            state = normalize_string(record["STATE"]).capitalize()
            postcode = normalize_string(record["POSTCODE"])

            station = (
                s.query(Station)
                .filter(Station.network_code == duid)
                .one_or_none()
            )

            if not station:
                station = Station(
                    code=duid,
                    network_code=duid,
                    created_by="au.nem.mms.stations",
                )

                records_created += 1
                created = True
            else:
                station.updated_by = "au.nem.mms.stations"
                records_updated += 1

            station.name = name
            station.network_id = "NEM"
            station.network_name = network_name
            station.address1 = address1
            station.address2 = address2
            station.locality = city
            station.state = state
            station.postcode = postcode

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


class NemStoreMMSStationStatus(DatabaseStoreBase):
    """

    """

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        for record in item:
            duid = normalize_duid(record["STATIONID"])
            # authorized_date = name_normalizer(record["AUTHORISEDDATE"])

            # @TODO this needs to be mapped to v3 state
            status = record["STATUS"]

            station = (
                s.query(Station)
                .filter(Station.network_code == duid)
                .one_or_none()
            )

            if not station:
                logger.error("Could not find station {}".format(duid))
                continue

            # @TODO station statuses -> facilities should be
            # set to retired if active

            try:
                s.add(station)
                s.commit()
            except Exception as e:
                logger.error(e)


class NemStoreMMSParticipant(DatabaseStoreBase):
    """

        @NOTE This pipeline has been converted to use pydantic models
    """

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        records_updated = 0
        records_created = 0

        q = self.engine.execute(text("select code from participant"))

        participant_codes = list(set([i[0] for i in q.fetchall()]))

        records = item

        for record in records:
            created = False

            if not "NAME" in record or not "PARTICIPANTID" in record:
                logger.error(record)
                raise Exception(
                    "Invalid MMS participant record: {}".format(record)
                )

            participant_schema = None

            try:
                participant_schema = ParticipantSchema(
                    **{
                        "code": record["PARTICIPANTID"],
                        "name": record["NAME"],
                        "network_name": record["NAME"],
                    }
                )
            except Exception:
                logger.error(
                    "Validation error with record: {}".format(record["NAME"])
                )
                continue

            # pid = normalize_duid(record["PARTICIPANTID"])
            # name = normalize_string(record["NAME"])
            # name_clean = participant_name_filter(record["NAME"])

            participant = (
                s.query(ParticipantModel)
                .filter(ParticipantModel.code == participant_schema.code)
                .one_or_none()
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


class NemStoreMMSDudetail(DatabaseStoreBase):
    """

    """

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        records_updated = 0
        records_created = 0

        for record in item:
            created = False

            duid = normalize_duid(record["DUID"])
            capacity_registered = clean_capacity(record["REGISTEREDCAPACITY"])
            capacity_max = clean_capacity(record["MAXCAPACITY"])
            dispatch_type = parse_dispatch_type(record["DISPATCHTYPE"])

            facility = (
                s.query(Facility)
                .filter(Facility.network_code == duid)
                .one_or_none()
            )

            if not facility:
                facility = Facility(
                    code=duid,
                    network_code=duid,
                    status_id="retired",
                    dispatch_type=dispatch_type,
                    created_by="au.nem.mms.dudetail",
                )

                records_created += 1
                created = True
            else:
                facility.updated_by = "au.nem.mms.dudetail"
                records_updated += 1

            facility.capacity_registered = capacity_registered
            facility.capacity_max = capacity_max

            try:
                s.add(facility)
                s.commit()
            except Exception as e:
                logger.error(e)

            logger.debug(
                "MMS Dudetail: {} facility record with id {}".format(
                    "Created" if created else "Updated", duid
                )
            )

        logger.info(
            "MMS Dudetail:Created {} facility records and updated {}".format(
                records_created, records_updated
            )
        )


class NemStoreMMSDudetailSummary(DatabaseStoreBase):
    """

    """

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        records_updated = 0
        records_created = 0

        for record in item:
            created = False

            participant_code = normalize_duid(
                record["facilities"][0]["PARTICIPANTID"]
            )

            # Step 1. Find participant by code or create
            participant = (
                s.query(ParticipantModel)
                .filter(ParticipantModel.code == participant_code)
                .one_or_none()
            )

            if not participant:
                participant = ParticipantModel(
                    code=participant_code,
                    network_code=participant_code,
                    created_by="au.nem.mms.dudetail_summary",
                )
                logger.debug("Created participant {}".format(participant_code))
            else:
                participant.updated_by = "au.nem.mms.dudetail_summary"

            # Step 3. now create the facilities and associate
            for facility_record in record["facilities"]:
                duid = normalize_duid(facility_record["DUID"])
                station_code = facility_map_station(
                    duid, normalize_duid(record["id"])
                )

                network_region = normalize_aemo_region(
                    facility_record["REGIONID"]
                )
                date_start = facility_record["date_start"]
                date_end = facility_record["date_end"]
                facility_state = "retired"

                # Step 2. Find station or create
                station = (
                    s.query(Station)
                    .filter(Station.network_code == station_code)
                    .one_or_none()
                )

                if not station:
                    station = Station(
                        code=station_code,
                        network_code=station_code,
                        network_id="NEM",
                        created_by="au.nem.mms.dudetail_summary",
                    )
                    logger.debug("Created station {}".format(station_code))
                else:
                    station.updated_by = "au.nem.mms.dudetail_summary"

                station.participant = participant

                if date_end == None:
                    facility_state = "operating"

                if not "DISPATCHTYPE" in facility_record:
                    logger.error(
                        "MMS dudetailsummary: Invalid record: {}".format(
                            facility_record
                        )
                    )
                    continue

                dispatch_type = parse_dispatch_type(
                    facility_record["DISPATCHTYPE"]
                )

                facility = (
                    s.query(Facility)
                    .filter(Facility.network_code == duid)
                    .one_or_none()
                )

                if not facility:

                    facility = Facility(
                        code=duid,
                        network_code=duid,
                        dispatch_type=dispatch_type,
                        created_by="au.nem.mms.dudetail_summary",
                    )

                    records_created += 1
                    created = True
                else:
                    facility.updated_by = "au.nem.mms.dudetail_summary"
                    records_updated += 1

                facility.network_region = network_region
                facility.deregistered = date_end
                facility.registered = date_start

                facility.status_id = facility_state

                if not facility.dispatch_type:
                    facility.dispatch_type = dispatch_type

                # Associations
                facility_station_id = facility_map_station(duid, station.id)

                facility.station_id = station.id

                try:
                    s.add(facility)
                    s.commit()
                except Exception as e:
                    logger.error(e)

            logger.debug(
                "MMS DudetailSummary:{} facility record with id {}".format(
                    "Created" if created else "Updated", duid
                )
            )

        logger.info(
            "MMS DudetailSummary: Created {} facility records and updated {}".format(
                records_created, records_updated
            )
        )


class NemStoreMMSStatdualloc(DatabaseStoreBase):
    """
        AEMO MMS associates all duids with station ids
    """

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        records_updated = 0
        records_created = 0

        for record in item:
            created = False

            duid = normalize_duid(record["DUID"])
            station_code = facility_map_station(
                duid, normalize_duid(record["STATIONID"])
            )

            station = (
                s.query(Station)
                .filter(Station.network_code == station_code)
                .one_or_none()
            )

            facility = (
                s.query(Facility)
                .filter(Facility.network_code == duid)
                .one_or_none()
            )

            if not station:
                station = Station(
                    code=station_code,
                    network_code=station_code,
                    network_id="NEM",
                    created_by="au.nem.mms.statdualloc",
                )

            if not facility:
                facility = Facility(
                    code=duid,
                    network_code=duid,
                    network_id="NEM",
                    status_id="retired",
                    created_by="au.nem.mms.statdualloc",
                )

                records_created += 1
                created = True
            else:
                facility.updated_by = "au.nem.mms.statdualloc"
                records_updated += 1

            facility.station = station

            try:
                s.add(facility)
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
