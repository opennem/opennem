import logging

from sqlalchemy.dialects.postgresql import insert

from opennem.db import SessionLocal, get_database_engine, get_database_session
from opennem.db.models.opennem import Facility, FacilityScada
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class NPIStoreFacility(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if "records" not in item:
            logger.error("Invalid return response")

        records = item["records"]

        engine = get_database_engine()
        session = SessionLocal()

        records_to_store = []

        for record in records:
            records_to_store.append(
                {
                    # "network_id": "WEM" if state == "WA" else "NEM",
                    # "trading_interval": interval_time,
                    # "facility_code": facility_code,
                    # "generated": generated,
                }
            )

        # free
        primary_keys = None

        stmt = insert(FacilityScada).values(records_to_store)
        stmt.bind = engine
        stmt = stmt.on_conflict_do_update(
            index_elements=["trading_interval", "network_id", "facility_code"],
            set_={"generated": stmt.excluded.generated,},
        )

        try:
            session.execute(stmt)
            session.commit()
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            session.close()

        return len(records_to_store)
