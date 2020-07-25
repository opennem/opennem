import csv
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from opennem.core.fueltechs import lookup_fueltech
from opennem.db.models.opennem import Facility, Participant
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

            participant_code = row["Participant Code"]
            participant = (
                s.query(Participant)
                .filter(Participant.code == participant_code)
                .one_or_none()
            )

            if not participant:
                print(
                    "Participant not found creating new database entry: {}".format(
                        participant_code
                    )
                )
                participant = Participant(
                    code=participant_code, name=row["Participant Name"]
                )
                s.add(participant)
                s.commit()

            facility = None

            facility_code = row["Facility Code"]
            facility = (
                s.query(Facility)
                .filter(Facility.code == facility_code)
                .one_or_none()
            )

            if not facility:
                print("Adding WEM facility: {}".format(facility_code))
                facility = Facility(
                    code=facility_code, participant=participant,
                )

            facility.active = (
                False if row["Balancing Status"] == "Non-Active" else True
            )

            if row["Capacity Credits (MW)"]:
                facility.capacity_credits = row["Capacity Credits (MW)"]

            if row["Maximum Capacity (MW)"]:
                facility.capacity_maximum = row["Maximum Capacity (MW)"]

            registered_date = row["Registered From"]

            if registered_date:
                registered_date_dt = datetime.strptime(
                    registered_date, "%Y-%m-%d %H:%M:%S"
                )
                facility.registered = registered_date_dt

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

            participant_code = row["PARTICIPANT_CODE"]
            participant = (
                s.query(Participant)
                .filter(Participant.code == participant_code)
                .one_or_none()
            )

            if not participant:
                print("Participant not found: {}".format(participant_code))
                participant = Participant(code=participant_code,)
                s.add(participant)
                s.commit()

            facility = None

            facility_code = row["FACILITY_CODE"]
            facility = (
                s.query(Facility)
                .filter(Facility.code == facility_code)
                .one_or_none()
            )

            if not facility:
                facility = Facility(
                    code=facility_code, participant=participant,
                )

            facility.name = row["DISPLAY_NAME"]

            if row["YEAR_COMMISSIONED"]:
                facility.comissioned = datetime.strptime(
                    row["YEAR_COMMISSIONED"], "%Y"
                )

            if row["CAPACITY_CREDITS"]:
                facility.capacity_credits = row["CAPACITY_CREDITS"]

            registered_date = row["REGISTRATION_DATE"]

            if registered_date:
                registered_date_dt = None

                date_fmt = "%Y-%m-%d %H:%M:%S"

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

            # if facility.geom:
            lat = row["LATITUDE"]
            lng = row["LONGITUDE"]
            facility.geom = "SRID=4326;POINT({} {})".format(lat, lng)

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
