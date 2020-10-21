import logging

import pytz
from sqlalchemy.dialects.postgresql import insert

from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import BomObservation
from opennem.utils.dates import parse_date
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)

STATE_TO_TIMEZONE = {
    "QLD": "Australia/Brisbane",
    "NSW": "Australia/Sydney",
    "VIC": "Australia/Melbourne",
    "TAS": "Australia/Hobart",
    "SA": "Australia/Adelaide",
    "NT": "Australia/Darwin",
    "WA": "Australia/Perth",
}


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

        if "header" not in item:
            logger.error("No header in bom observation")
            return 0

        header = item["header"]

        if "state_time_zone" not in header:
            print(header)
            logger.error("No state timezone in header")
            return 0

        timezone_state: str = header["state_time_zone"].strip().upper()

        if timezone_state not in STATE_TO_TIMEZONE.keys():
            logger.error("No timezone for state: %s", timezone_state)

        timezone = pytz.timezone(STATE_TO_TIMEZONE[timezone_state])

        for obs in records:
            observation_time = parse_date(
                obs["aifstime_utc"], dayfirst=False, is_utc=True
            ).astimezone(timezone)

            code = obs["code"]

            if not observation_time or not code:
                continue

            records_to_store.append(
                {
                    "station_id": code,
                    "observation_time": observation_time,
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

        if not len(records_to_store):
            return 0

        stmt = insert(BomObservation).values(records_to_store)
        stmt.bind = engine
        stmt = stmt.on_conflict_do_update(
            index_elements=["observation_time", "station_id"],
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
