import logging
from datetime import datetime
from typing import Optional

import pytz
from sqlalchemy.dialects.postgresql import insert

from opennem.clients.bom import BOMObservationReturn
from opennem.controllers.schema import ControllerReturn
from opennem.db import get_database_engine, get_scoped_session
from opennem.db.models.opennem import BomObservation

logger = logging.getLogger(__name__)


def store_bom_observation_intervals(observations: BOMObservationReturn) -> ControllerReturn:
    """Store BOM Observations"""

    session = get_scoped_session()
    engine = get_database_engine()

    cr = ControllerReturn(total_records=len(observations.observations))

    latest_forecast: Optional[datetime] = max(
        [o.observation_time for o in observations.observations]
    )

    if latest_forecast:
        latest_forecast = latest_forecast.astimezone(pytz.timezone("Australia/Sydney"))
        logger.debug("server_latest is {}".format(latest_forecast))

        cr.server_latest = latest_forecast

    records_to_store = []

    for obs in observations.observations:
        records_to_store.append(
            {
                "station_id": observations.station_code,
                "observation_time": obs.observation_time,
                "temp_apparent": obs.apparent_t,
                "temp_air": obs.air_temp,
                "press_qnh": obs.press_qnh,
                "wind_dir": obs.wind_dir,
                "wind_spd": obs.wind_spd_kmh,
                "wind_gust": obs.gust_kmh,
                "cloud": obs.cloud,
                "cloud_type": obs.cloud_type,
                "humidity": obs.rel_hum,
            }
        )
        cr.processed_records += 1

    if not len(records_to_store):
        return cr

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
        cr.errors = cr.processed_records
        cr.error_detail = str(e)
        return cr
    finally:
        session.close()
        engine.dispose()

    cr.inserted_records = cr.processed_records

    return cr
