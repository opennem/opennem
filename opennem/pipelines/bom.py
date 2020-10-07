import logging
from datetime import datetime

from sqlalchemy.orm import sessionmaker

from opennem.db import SessionLocal
from opennem.db.models.opennem import BomObservation
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


def parse_date(date_str):
    dt = datetime.strptime(date_str, "%Y%m%d%H%M%S")

    return dt


class StoreBomObservation(object):
    """
        Pipeline to store BOM observations into the database
    """

    @check_spider_pipeline
    def process_item(self, item, spider):

        s = SessionLocal()

        observation = BomObservation(
            station_id=item["station_id"],
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
