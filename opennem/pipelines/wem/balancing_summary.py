import csv
import logging

from sqlalchemy.dialects.postgresql import insert

from opennem.db.models.opennem import BalancingSummary
from opennem.pipelines import DatabaseStoreBase
from opennem.schema.network import NetworkWEM
from opennem.utils.dates import parse_date
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class WemStoreBalancingSummary(DatabaseStoreBase):
    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        csvreader = csv.DictReader(item["content"].split("\n"))

        records_to_store = []

        for record in csvreader:
            trading_interval = parse_date(
                record["Trading Interval"], network=NetworkWEM
            )

            if not trading_interval:
                continue

            records_to_store.append(
                {
                    "created_by": spider.name,
                    "network_id": "WEM",
                    "network_region": "WEM",
                    "trading_interval": trading_interval,
                    "forecast_load": record["Load Forecast (MW)"],
                    "generation_scheduled": record[
                        "Scheduled Generation (MW)"
                    ],
                    "generation_non_scheduled": record[
                        "Non-Scheduled Generation (MW)"
                    ],
                    "generation_total": record["Total Generation (MW)"],
                    "price": record["Final Price ($/MWh)"],
                }
            )

        stmt = insert(BalancingSummary).values(records_to_store)
        stmt.bind = self.engine
        stmt = stmt.on_conflict_do_update(
            index_elements=[
                "trading_interval",
                "network_id",
                "network_region",
            ],
            set_={
                "price": stmt.excluded.price,
                "generation_total": stmt.excluded.generation_total,
            },
        )

        try:
            s.execute(stmt)
            s.commit()
        except Exception as e:
            logger.error("Error inserting records")
            logger.error(e)
            return 0
        finally:
            s.close()

        return len(records_to_store)
