import logging

from sqlalchemy.dialects.postgresql import insert

from opennem.db import SessionLocal, get_database_engine, get_database_session
from opennem.db.models.opennem import Facility, FacilityScada
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import parse_date
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


STATE_POSTCODE_PREFIXES = {
    "NSW": "2",
    "VIC": "3",
    "QLD": "4",
    "SA": "5",
    "WA": "6",
    "TAS": "7",
    "NT": "0",
}

from opennem.importer.apvi import ROOFTOP_CODE


class APVIStoreData(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if "records" not in item:
            logger.error("Invalid return response")

        records = item["records"]

        if "postcode" not in records:
            logger.error("No postcode data")

        postcode_gen = records["postcode"]

        engine = get_database_engine()
        session = SessionLocal()

        records_to_store = []
        primary_keys = []

        for record in postcode_gen:
            nem_interval = parse_date(
                record["ts"], network=NetworkNEM, dayfirst=False
            )

            for state, prefix in STATE_POSTCODE_PREFIXES.items():
                generated = sum(
                    [v for k, v in record.items() if k.startswith(prefix)]
                )

                facility_code = "{}_{}".format(ROOFTOP_CODE, state.upper())

                records_to_store.append(
                    {
                        "network_id": "WEM" if state == "WA" else "NEM",
                        "trading_interval": nem_interval,
                        "facility_code": facility_code,
                        "generated": generated,
                    }
                )

        # free
        primary_keys = None

        stmt = insert(FacilityScada).values(records_to_store)
        stmt.bind = engine
        stmt = stmt.on_conflict_do_update(
            constraint="facility_scada_pkey",
            set_={
                "eoi_quantity": stmt.excluded.eoi_quantity,
                "generated": stmt.excluded.generated,
            },
        )

        try:
            session.execute(stmt)
            session.commit()
        except Exception as e:
            logger.error("Error: {}".format(e))
        finally:
            session.close()

        return len(records_to_store)
