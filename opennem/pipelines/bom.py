import csv
import logging
from datetime import datetime

from scrapy.exceptions import DropItem
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from opennem.db import db_connect
from opennem.db.models.bom import BomObservation
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


def parse_date(date_str):
    dt = datetime.strptime(date_str, "%Y%m%d%H%M%S")

    return dt


class DatabaseStoreBase(object):
    def __init__(self):
        engine = db_connect()
        self.session = sessionmaker(bind=engine)


class StoreBomObservation(DatabaseStoreBase):
    @check_spider_pipeline
    def process_item(self, item, spider):

        s = self.session()

        print(item)

        observation = BomObservation(
            station_id=spider.observatory_id,
            observation_time=parse_date(item["aifstime_utc"]),
            temp_apparent=item["apparent_t"],
            temp_air=item["air_temp"],
            press_qnh=item["press_qnh"],
            wind_dir=item["wind_dir"],
            wind_spd=item["wind_spd_kmh"],
        )

        try:
            s.add(observation)
            s.commit()
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            s.close()

        return item
