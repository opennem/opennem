import logging

from sqlalchemy.dialects.postgresql import insert

from opennem.core.normalizers import clean_float
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import BalancingSummary
from opennem.schema.network import NetworkNEM
from opennem.utils.dates import parse_date
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger("opennem.pipeline.nem.summary")


class NemwebSummaryPipeline(object):
    @check_spider_pipeline
    def process_item(self, item, spider=None):
        if not item:
            logger.error("No item in pipeline")
            return None

        if "content" not in item:
            logger.error("No content in pipeline")
            return None

        content = item["content"]

        if "ELEC_NEM_SUMMARY" not in content:
            logger.error("Invalid summary return")
            return None

        summary = content["ELEC_NEM_SUMMARY"]

        s = SessionLocal()
        records_to_store = []

        for row in summary:
            trading_interval = parse_date(row["SETTLEMENTDATE"], network=NetworkNEM)

            demand_total = clean_float(row["TOTALDEMAND"])
            generation_scheduled = clean_float(row["SCHEDULEDGENERATION"])
            generation_non_scheduled = clean_float(row["SEMISCHEDULEDGENERATION"])

            records_to_store.append(
                {
                    "created_by": spider.name,
                    "trading_interval": trading_interval,
                    "network_id": "NEM",
                    "network_region": row["REGIONID"].strip(),
                    "demand_total": demand_total,
                    "generation_scheduled": generation_scheduled,
                    "generation_non_scheduled": generation_non_scheduled,
                }
            )

        stmt = insert(BalancingSummary).values(records_to_store)
        stmt.bind = get_database_engine()
        stmt = stmt.on_conflict_do_update(
            index_elements=[
                "trading_interval",
                "network_id",
                "network_region",
            ],
            set_={
                "demand_total": stmt.excluded.demand_total,
                "generation_scheduled": stmt.excluded.generation_scheduled,
                "generation_non_scheduled": stmt.excluded.generation_non_scheduled,
            },
        )

        try:
            s.execute(stmt)
            s.commit()
        except Exception as e:
            logger.error("Error inserting records")
            logger.error(e)
            return {"num_records": 0}
        finally:
            s.close()

        return {"num_records": len(records_to_store)}
