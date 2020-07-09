import csv
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from opennem.db.models.wem import WemParticipant
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)

# @TODO we can probably merge these two pipelines now


class WemStoreParticipant(DatabaseStoreBase):
    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        record_count = 0
        csvreader = csv.DictReader(item["content"].split("\n"))

        for row in csvreader:
            if not "Participant Code" in row:
                logger.error("Invalid row")
                continue

            participant = None

            participant_code = row["Participant Code"]
            participant = (
                s.query(WemParticipant)
                .filter(WemParticipant.code == participant_code)
                .one_or_none()
            )

            if not participant:
                print("Participant not found: {}".format(participant_code))
                participant = WemParticipant(
                    code=row["Participant Code"],
                    name=row["Participant Name"],
                    address=row["Address"],
                    city=row["City"],
                    state=row["State"],
                    postcode=row["Postcode"],
                )
            else:
                participant.name = row["Participant Name"]
                participant.name = row["Participant Name"]
                participant.address = row["Address"]
                participant.city = row["City"]
                participant.state = row["State"]
                participant.postcode = row["Postcode"]

            try:
                s.add(participant)
                s.commit()
                record_count += 1
            except Exception as e:
                logger.error(e)

        s.close()

        return record_count


class WemStoreLiveParticipant(DatabaseStoreBase):
    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        record_count = 0
        csvreader = csv.DictReader(item["content"].split("\n"))

        for row in csvreader:
            if not "PARTICIPANT_CODE" in row:
                logger.error("Invalid row")
                continue

            participant = None

            participant_code = row["PARTICIPANT_CODE"]
            participant = (
                s.query(WemParticipant)
                .filter(WemParticipant.code == participant_code)
                .one_or_none()
            )

            if not participant:
                print("Participant not found: {}".format(participant_code))
                participant = WemParticipant(
                    code=participant_code,
                    name=row["PARTICIPANT_DISPLAY_NAME"],
                )
            else:
                participant.name = row["PARTICIPANT_DISPLAY_NAME"]

            try:
                s.add(participant)
                s.commit()
                record_count += 1
            except Exception as e:
                logger.error(e)

        s.close()

        return record_count
