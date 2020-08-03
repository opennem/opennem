import csv
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from opennem.core.normalizers import (
    normalize_duid,
    normalize_string,
    participant_name_filter,
)
from opennem.db.models.opennem import Participant
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
                s.query(Participant)
                .filter(Participant.code == participant_code)
                .one_or_none()
            )

            if not participant:
                print("Participant not found: {}".format(participant_code))
                participant = Participant(
                    code=row["Participant Code"],
                    name=row["Participant Name"],
                    address=row["Address"],
                    city=row["City"],
                    state=row["State"],
                    postcode=row["Postcode"],
                    created_by="pipeline.wem.participant",
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
            created_record = False

            participant_code = normalize_string(row["PARTICIPANT_CODE"])
            participant_name = participant_name_filter(
                row["PARTICIPANT_DISPLAY_NAME"]
            )

            participant = (
                s.query(Participant)
                .filter(Participant.code == participant_code)
                .one_or_none()
            )

            if not participant:
                logger.debug(
                    "Participant not found: {}".format(participant_code)
                )

                participant = Participant(
                    code=participant_code,
                    name=participant_name,
                    created_by="pipeline.wem.live.participant",
                )
                created_record = True
            elif participant.name != participant_name:
                participant.name = participant_name
                participant.updated_by = "pipeline.wem.live.participant"

            try:
                s.add(participant)
                s.commit()
                record_count += 1
            except Exception as e:
                logger.error(e)

        s.close()

        return record_count
