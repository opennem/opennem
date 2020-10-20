import csv
import logging
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from opennem.core.facility_code import parse_wem_facility_code
from opennem.core.fueltechs import lookup_fueltech
from opennem.core.normalizers import (
    clean_capacity,
    normalize_duid,
    normalize_string,
    participant_name_filter,
    station_name_cleaner,
)
from opennem.db import SessionLocal
from opennem.db.models.opennem import Facility, Location, Participant, Station
from opennem.schema.network import NetworkWEM
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class WemStoreFacility(object):
    @check_spider_pipeline
    def process_item(self, item, spider):
        s = SessionLocal()

        records_added = 0
        csvreader = csv.DictReader(item["content"].split("\n"))

        for row in csvreader:

            if "Participant Code" not in row:
                logger.error("Invalid row")
                continue

            if row["Facility Type"] in [
                "Demand Side Program",
                "Non-Dispatchable Load",
                "Network",
            ]:
                continue

            participant = None

            participant_name = participant_name_filter(row["Participant Name"])
            participant_network_name = normalize_string(
                row["Participant Name"]
            )
            participant_code = normalize_duid(row["Participant Code"])

            participant = (
                s.query(Participant)
                .filter(Participant.code == participant_code)
                .one_or_none()
            )

            if not participant:
                participant = Participant(
                    created_by=spider.name,
                    approved_at=datetime.now(),
                    code=participant_code,
                    name=participant_name,
                    network_name=participant_network_name,
                )
                s.add(participant)
                s.commit()

                logger.debug(
                    "Participant not found created new database entry: %s",
                    participant_code,
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
                    created_by="opennem.wem.facilities",
                    approved_at=datetime.now(),
                    code=station_code,
                    network_code=station_code,
                    participant=participant,
                )

                location = Location(state="WA")

                station.location = location

                logger.debug("Added WEM station: {}".format(station_code))

            facility = (
                s.query(Facility)
                .filter(Facility.code == facility_code)
                .one_or_none()
            )

            if not facility:
                facility = Facility(
                    created_by=spider.name,
                    approved_at=datetime.now(),
                    code=facility_code,
                    network_id="WEM",
                    network_code=facility_code,
                    network_region="WEM",
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


class WemStoreLiveFacilities(object):
    def parse_interval(self, date_str):
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        dt_aware = NetworkWEM.get_timezone().localize(dt)

        return dt_aware

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = SessionLocal()

        records_added = 0
        csvreader = csv.DictReader(item["content"].split("\n"))

        for row in csvreader:

            if "PARTICIPANT_CODE" not in row:
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
                    created_by=spider.name,
                    approved_by=spider.name,
                    approved_at=datetime.now(),
                    code=participant_code,
                    network_code=participant_code,
                    network="WEM",
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
                    created_by=spider.name,
                    approved_by=spider.name,
                    approved_at=datetime.now(),
                    code=station_code,
                    network_code=station_code,
                    participant=participant,
                )

                location = Location(state="WA")
                s.add(location)

                station.location = location

                logger.debug("Added WEM station: {}".format(station_code))

            lat = row["LATITUDE"]
            lng = row["LONGITUDE"]

            station.name = station_name
            station.network_name = station_network_name

            if lat and lng and not station.location.geom:
                station.location.geom = "SRID=4326;POINT({} {})".format(
                    lat, lng
                )
                station.location.geocode_by = "aemo"
                station.location.geocode_approved = True

            facility = (
                s.query(Facility)
                .filter(Facility.code == facility_code)
                .one_or_none()
            )

            if not facility:
                facility = Facility(
                    created_by="opennem.wem.live.facilities",
                    approved_at=datetime.now(),
                    network_id="WEM",
                    code=facility_code,
                    network_code=facility_code,
                    network_region="WEM",
                )

            registered_date = row["YEAR_COMMISSIONED"]

            if registered_date:
                registered_date_dt = None

                date_fmt = "%Y"

                try:
                    registered_date_dt = datetime.strptime(
                        registered_date, date_fmt
                    )
                except Exception:
                    logger.error(
                        "Bad date: %s for format %s", registered_date, date_fmt
                    )

                if registered_date_dt:
                    facility.registered = registered_date_dt

            fueltech = lookup_fueltech(
                fueltype=row["PRIMARY_FUEL"], techtype=row["FACILITY_TYPE"]
            )

            if fueltech and not facility.fueltech:
                facility.fueltech_id = fueltech

            facility.status_id = "operating"
            facility.station = station

            s.add(station)
            s.add(facility)
            s.commit()
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
