import logging

from sqlalchemy.dialects.postgresql import insert

from opennem.db import SessionLocal, get_database_engine
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

        session = SessionLocal()
        engine = get_database_engine()

        records_to_store = []

        if "records" not in item:

            return 0
        records = item["records"]

        for obs in records:
            records_to_store.append(
                {
                    "station_id": obs["code"],
                    "observation_time": parse_date(
                        obs["aifstime_utc"], dayfirst=False, is_utc=True
                    ),
                    "temp_apparent": obs["apparent_t"],
                    "temp_air": obs["air_temp"],
                    "press_qnh": obs["press_qnh"],
                    "wind_dir": obs["wind_dir"],
                    "wind_spd": obs["wind_spd_kmh"],
                    "wind_gust": obs["gust_kmh"],
                    "cloud": obs["cloud"].replace("-", ""),
                    "cloud_type": obs["cloud_type"].replace("-", ""),
                    "humidity": obs["rel_hum"],
                }
            )

        stmt = insert(BomObservation).values(records_to_store)
        stmt.bind = engine
        stmt = stmt.on_conflict_do_update(
            constraint="bom_observation_pkey",
            set_={
                "temp_apparent": stmt.excluded.temp_apparent,
                "temp_air": stmt.excluded.temp_air,
                "press_qnh": stmt.excluded.press_qnh,
                "wind_dir": stmt.excluded.wind_dir,
                "wind_spd": stmt.excluded.wind_spd,
                "wind_gust": stmt.excluded.wind_gust,
                "cloud": stmt.excluded.cloud,
                "cloud_type": stmt.excluded.cloud_type,
                "humidity": stmt.excluded.humidity,
            },
        )

        try:
            session.execute(stmt)
            session.commit()
        except Exception as e:
            logger.error("Error: {}".format(e))
            return 0
        finally:
            session.close()

        return len(records_to_store)
