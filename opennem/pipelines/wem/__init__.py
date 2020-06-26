import csv
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError

from opennem.db.models.wem import (
    WemBalancingSummary,
    WemFacility,
    WemFacilityScada,
    WemParticipant,
)
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class WemStoreFacility(DatabaseStoreBase):
    @check_spider_pipeline
    def process_item(self, item, spider):
        s = self.session()

        if not "Participant Code" in item:
            print("invlid row")
            return item

        participant = None

        participant_code = item["Participant Code"]
        participant = s.query(WemParticipant).get(participant_code)

        if not participant:
            print("Participant not found: {}".format(participant_code))
            participant = WemParticipant(
                code=participant_code, name=item["Participant Name"]
            )
            s.add(participant)
            s.commit()

        facility = None

        facility_code = item["Facility Code"]
        facility = s.query(WemFacility).get(facility_code)

        if not facility:
            facility = WemFacility(
                code=facility_code, participant=participant,
            )

        facility.active = (
            False if item["Balancing Status"] == "Non-Active" else True
        )

        if item["Capacity Credits (MW)"]:
            facility.capacity_credits = item["Capacity Credits (MW)"]

        if item["Maximum Capacity (MW)"]:
            facility.capacity_maximum = item["Maximum Capacity (MW)"]

        registered_date = item["Registered From"]

        if registered_date:
            registered_date_dt = datetime.strptime(
                registered_date, "%Y-%m-%d %H:%M:%S"
            )
            facility.registered = registered_date_dt

        try:
            s.add(facility)
            s.commit()
        except IntegrityError as e:
            pass
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            s.close()

        return item


class WemStoreFacilityScada(DatabaseStoreBase):
    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        if not "Participant Code" in item:
            print("invlid row")
            return item

        trading_interval = item["Trading Interval"]

        trading_interval_dt = datetime.strptime(
            trading_interval, "%Y-%m-%d %H:%M:%S"
        )

        # @TODO we possibly need to shift eoi_quantity back a time period

        facility_scada = WemFacilityScada(
            trading_interval=trading_interval_dt,
            facility_id=item["Facility Code"],
            eoi_quantity=item["EOI Quantity (MW)"],
            generated=item["Energy Generated (MWh)"],
        )

        try:
            s.add(facility_scada)
            s.commit()
        except IntegrityError as e:
            pass
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            s.close()

        return item
