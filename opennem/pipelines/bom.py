import logging

from opennem.db import SessionLocal
from opennem.db.models.opennem import BomObservation
from opennem.utils.dates import parse_date
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class StoreBomObservation(object):
    """
        Pipeline to store BOM observations into the database
    """

    @check_spider_pipeline
    def process_item(self, item, spider):

        s = SessionLocal()

        observation = BomObservation(
            station_id=item["code"],
            observation_time=parse_date(
                item["aifstime_utc"], dayfirst=False, is_utc=True
            ),
            temp_apparent=item["apparent_t"],
            temp_air=item["air_temp"],
            press_qnh=item["press_qnh"],
            wind_dir=item["wind_dir"],
            wind_spd=item["wind_spd_kmh"],
            wind_gust=item["gust_kmh"],
            cloud=item["cloud"],
            cloud_type=item["cloud_type"],
            humidity=item["rel_hum"],
        )

        try:
            s.add(observation)
            s.commit()
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            s.close()

        return item
