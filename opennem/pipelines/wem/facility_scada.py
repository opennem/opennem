import csv
import logging
from datetime import datetime, timedelta

from sqlalchemy.dialects.postgresql import insert

from opennem.core.normalizers import normalize_duid
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import FacilityScada
from opennem.pipelines import DatabaseStoreBase
from opennem.schema.network import NetworkWEM
from opennem.utils.dates import parse_date
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class WemStoreFacilityScada(DatabaseStoreBase):
    @check_spider_pipeline
    def process_item(self, item, spider=None):

        session = SessionLocal()
        engine = get_database_engine()

        csvreader = csv.DictReader(item["content"].split("\n"))

        records_to_store = []
        primary_keys = []

        for row in csvreader:
            trading_interval = parse_date(
                row["Trading Interval"], network=NetworkWEM
            )
            facility_code = normalize_duid(row["Facility Code"])

            __key = (trading_interval, facility_code)

            if __key not in primary_keys:
                records_to_store.append(
                    {
                        "network_id": "WEM",
                        "trading_interval": trading_interval,
                        "facility_code": facility_code,
                        "eoi_quantity": row["EOI Quantity (MW)"] or None,
                        "generated": row["Energy Generated (MWh)"] or None,
                    }
                )
                primary_keys.append(__key)

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


class WemStoreLiveFacilityScada(DatabaseStoreBase):
    """
        Store live facility scada data.

    """

    @check_spider_pipeline
    def process_item(self, item, spider=None):

        session = SessionLocal()
        engine = get_database_engine()

        csvreader = csv.DictReader(item["content"].split("\n"))

        records_to_store = []
        last_asat = None

        for row in csvreader:
            if row["AS_AT"] != "":
                last_asat = parse_date(row["AS_AT"], network=NetworkWEM)

            if not last_asat or type(last_asat) is not datetime:
                logger.error("Invalid row or no datetime")
                continue

            # We need to pivot the table since columns are time intervals
            for i in range(1, 48):

                column = f"I{i:02}"

                if column not in row:
                    logger.error(
                        "Do not have data for interval {}".format(column)
                    )
                    continue

                if i > 0:
                    interval = last_asat - timedelta(minutes=(i - 1) * 30)
                else:
                    interval = last_asat

                facility_code = normalize_duid(row["FACILITY_CODE"])

                val = None

                try:
                    val = float(row[column]) / 2 or None
                except ValueError:
                    pass

                records_to_store.append(
                    {
                        "network_id": "WEM",
                        "trading_interval": interval,
                        "facility_code": facility_code,
                        "generated": val,
                    }
                )

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
            logger.error("Error inserting records")
            logger.error(e)
        finally:
            session.close()

        return len(records_to_store)
