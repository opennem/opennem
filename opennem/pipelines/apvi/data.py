import logging

from sqlalchemy.dialects.postgresql import insert

from opennem.db import SessionLocal, get_database_engine, get_database_session
from opennem.db.models.opennem import Facility, FacilityScada
from opennem.importer.apvi import ROOFTOP_CODE
from opennem.schema.network import NetworkNEM, NetworkWEM
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


class APVIStoreData(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if "records" not in item:
            logger.error("Invalid return response")

        records = item["records"]

        if "postcode" not in records:
            logger.error("No postcode data")

        if "installations" not in records:
            logger.error("No postcode data")

        if "postcodeCapacity" not in records:
            logger.error("No postcode capacity data")

        postcode_gen = records["postcode"]
        postcode_capacity = records["postcodeCapacity"]
        installations = records["installations"]

        engine = get_database_engine()
        session = SessionLocal()

        records_to_store = []

        for record in postcode_gen:
            for state, prefix in STATE_POSTCODE_PREFIXES.items():
                facility_code = "{}_{}".format(ROOFTOP_CODE, state.upper())

                network_network = NetworkWEM if state == "WA" else NetworkNEM

                interval_time = parse_date(
                    record["ts"], network=network_network, dayfirst=False
                )

                generated = sum(
                    [v for k, v in record.items() if k.startswith(prefix)]
                )

                records_to_store.append(
                    {
                        "network_id": "WEM" if state == "WA" else "NEM",
                        "trading_interval": interval_time,
                        "facility_code": facility_code,
                        "generated": generated,
                    }
                )

        STATE_CAPACITIES = {}

        for postcode_prefix, capacity_val in postcode_capacity.items():
            for state, prefix in STATE_POSTCODE_PREFIXES.items():
                if state not in STATE_CAPACITIES:
                    STATE_CAPACITIES[state] = 0

                if postcode_prefix.startswith(prefix):
                    STATE_CAPACITIES[state] += capacity_val

        for state, state_capacity in STATE_CAPACITIES.items():
            facility_code = "{}_{}".format(ROOFTOP_CODE, state.upper())

            state_facility: Facility = session.query(Facility).filter_by(
                code=facility_code
            ).one_or_none()

            state_facility.capacity_registered = state_capacity

            if state.lower() in installations:
                state_number_units = installations[state.lower()]
                state_facility.unit_number = state_number_units

            session.add(state_facility)
            session.commit()

        # free
        primary_keys = None

        stmt = insert(FacilityScada).values(records_to_store)
        stmt.bind = engine
        stmt = stmt.on_conflict_do_update(
            constraint="facility_scada_pkey",
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
