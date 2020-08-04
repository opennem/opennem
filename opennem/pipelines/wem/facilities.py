import csv
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from opennem.core.facility_code import parse_wem_facility_code
from opennem.core.fueltechs import lookup_fueltech
from opennem.core.normalizers import (
    clean_capacity,
    normalize_duid,
    normalize_string,
    participant_name_filter,
    station_name_cleaner,
)
from opennem.db.models.opennem import Facility, Participant, Station
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class WemStoreFacility(DatabaseStoreBase):
    @check_spider_pipeline
    def process_item(self, item, spider):
        s = self.session()

        records_added = 0
        csvreader = csv.DictReader(item["content"].split("\n"))

        for row in csvreader:

            if not "Participant Code" in row:
                logger.error("Invalid row")
                continue

            participant = None

            participant_name = participant_name_filter(row["Participant Name"])
            participant_network_name = normalize_string(
                row["Participant Name"]
            )
            participant_code = normalize_duid(row["Participant Code"])
            participant_network_code = normalize_duid(row["Participant Code"])

            participant = (
                s.query(Participant)
                .filter(Participant.code == participant_code)
                .one_or_none()
            )

            if not participant:
                participant = Participant(
                    code=participant_code,
                    name=participant_name,
                    network_name=participant_network_name,
                    created_by="pipeline.wem.facilities",
                )
                s.add(participant)
                s.commit()

                logger.debug(
                    "Participant not found created new database entry: {}".format(
                        participant_code
                    )
                )

            station = None
            facility = None

            facility_code = normalize_duid(row["Facility Code"])
            station_code = parse_wem_facility_code(facility_code)

            station = (
                s.query(Station)
                .filter(Station.code == station_code)
                .one_or_none()
            )

            if not station:
                station = Station(
                    code=station_code,
                    network_id="WEM",
                    network_code=station_code,
                    participant=participant,
                    created_by="pipeline.wem.facilities",
                )

                logger.debug("Added WEM station: {}".format(station_code))

            facility = (
                s.query(Facility)
                .filter(Facility.code == facility_code)
                .one_or_none()
            )

            if not facility:
                facility = Facility(
                    code=facility_code,
                    network_code=facility_code,
                    network_region="WEM",
                    created_by="pipeline.wem.facilities",
                )

            capacity_registered = clean_capacity(row["Maximum Capacity (MW)"])
            capacity_unit = clean_capacity(row["Maximum Capacity (MW)"])
            registered_date = row["Registered From"]

            facility.status_id = "operating"
            facility.capacity_registered = capacity_registered
            facility.unit_id = 1
            facility.unit_number = 1
            facility.unit_capacity = capacity_unit

            if registered_date:
                registered_date_dt = datetime.strptime(
                    registered_date, "%Y-%m-%d %H:%M:%S"
                )
                facility.registered = registered_date_dt

            facility.station = station

            s.add(facility)
            records_added += 1

        try:
            s.commit()
        except IntegrityError as e:
            logger.error(e)
            pass
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            s.close()

        return records_added


class WemStoreLiveFacilities(DatabaseStoreBase):
    def parse_interval(self, date_str):
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        records_added = 0
        csvreader = csv.DictReader(item["content"].split("\n"))

        for row in csvreader:

            if not "PARTICIPANT_CODE" in row:
                logger.error("Invalid row")
                continue

            participant = None

            participant_code = normalize_duid(row["PARTICIPANT_CODE"])

            participant = (
                s.query(Participant)
                .filter(Participant.code == participant_code)
                .one_or_none()
            )

            if not participant:
                participant = Participant(
                    code=participant_code,
                    network_code=participant_code,
                    network="WEM",
                    created_by="pipeline.wem.live_facilities",
                )
                s.add(participant)
                s.commit()

                logger.warning(
                    "Participant not found created new database entry: {}".format(
                        participant_code
                    )
                )

            station = None
            facility = None

            created_station = False
            created_facility = False

            facility_code = normalize_duid(row["FACILITY_CODE"])
            station_code = parse_wem_facility_code(facility_code)
            station_name = station_name_cleaner(row["DISPLAY_NAME"])
            station_network_name = normalize_string(row["DISPLAY_NAME"])

            station = (
                s.query(Station)
                .filter(Station.code == station_code)
                .one_or_none()
            )

            if not station:
                station = Station(
                    code=station_code,
                    network_id="WEM",
                    network_code=station_code,
                    participant=participant,
                    created_by="pipeline.wem.live.facilities",
                )

                created_station = True
                logger.debug("Added WEM station: {}".format(station_code))

            lat = row["LATITUDE"]
            lng = row["LONGITUDE"]

            station.name = station_name
            station.network_name = station_network_name

            if lat and lng and not station.geom:
                station.geom = "SRID=4326;POINT({} {})".format(lat, lng)
                station.geocode_by = "aemo"
                station.geocode_approved = True

            facility = (
                s.query(Facility)
                .filter(Facility.code == facility_code)
                .one_or_none()
            )

            if not facility:
                facility = Facility(
                    code=facility_code,
                    network_code=facility_code,
                    network_region="WEM",
                    created_by="pipeline.wem.live.facilities",
                )

                created_facility = True

            registered_date = row["YEAR_COMMISSIONED"]

            if registered_date:
                registered_date_dt = None

                date_fmt = "%Y"

                try:
                    registered_date_dt = datetime.strptime(
                        registered_date, date_fmt
                    )
                except Exception as e:
                    logger.error(
                        "Bad date: {} for format {}".format(
                            registered_date, date_fmt
                        )
                    )

                if registered_date_dt:
                    facility.registered = registered_date_dt

            fueltech = lookup_fueltech(row["PRIMARY_FUEL"])

            if fueltech and not facility.fueltech:
                facility.fueltech_id = fueltech

            facility.status_id = "operating"
            facility.station = station

            s.add(station)
            s.add(facility)
            records_added += 1

        try:
            s.commit()
        except IntegrityError as e:
            logger.error(e)
            pass
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            s.close()

        return records_added
