import csv
import logging

from opennem.core.normalizers import (
    normalize_duid,
    normalize_string,
    participant_name_filter,
)
from opennem.db import SessionLocal
from opennem.db.models.opennem import Participant
from opennem.pipelines import DatabaseStoreBase
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)

# @TODO we can probably merge these two pipelines now


class WemStoreParticipant(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = SessionLocal()

        record_count = 0
        csvreader = csv.DictReader(item["content"].split("\n"))

        for row in csvreader:
            if "Participant Code" not in row:
                logger.error("Invalid row")
                continue

            participant = None

            participant_code = normalize_duid(row["Participant Code"])
            participant_name = participant_name_filter(row["Participant Name"])

            participant = (
                s.query(Participant)
                .filter(Participant.code == participant_code)
                .one_or_none()
            )

            if not participant:
                participant = Participant(
                    code=participant_code,
                    name=participant_name,
                    # @TODO WEM provides these but nem doesn't so ignore for noe
                    # address=row["Address"],
                    # city=row["City"],
                    # state=row["State"],
                    # postcode=row["Postcode"],
                    created_by="pipeline.wem.participant",
                )

                logger.info(
                    "Created new WEM participant: {}".format(participant_code)
                )

            elif participant.name != participant_name:
                participant.name = participant_name
                participant.updated_by = "pipeline.wem.participant"
                logger.info(
                    "Updated WEM participant: {}".format(participant_code)
                )

            try:
                s.add(participant)
                s.commit()
                record_count += 1
            except Exception as e:
                logger.error(e)

        s.close()

        return record_count


class WemStoreLiveParticipant(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = SessionLocal()

        record_count = 0
        csvreader = csv.DictReader(item["content"].split("\n"))

        for row in csvreader:
            if "PARTICIPANT_CODE" not in row:
                logger.error("Invalid row")
                continue

            participant = None

            participant_code = normalize_duid(
                normalize_string(row["PARTICIPANT_CODE"])
            )
            participant_name = participant_name_filter(
                row["PARTICIPANT_DISPLAY_NAME"]
            ) or participant_name_filter(
                row.get("PARTICIPANT_FULL_NAME", None)
            )

            participant = (
                s.query(Participant)
                .filter(Participant.code == participant_code)
                .one_or_none()
            )

            if not participant:
                participant = Participant(
                    code=participant_code,
                    name=participant_name,
                    created_by=spider.name,
                )

                logger.info(
                    "Created new WEM participant: {}".format(participant_code)
                )

            elif participant.name != participant_name:
                participant.name = participant_name
                participant.updated_by = spider.name

                logger.info(
                    "Updated WEM participant: {}".format(participant_code)
                )

            try:
                s.add(participant)
                s.commit()
                record_count += 1
            except Exception as e:
                logger.error(e)

        s.close()

        return record_count
