import csv
import logging

from sqlalchemy.dialects.postgresql import insert

from opennem.db.models.opennem import BalancingSummary
from opennem.pipelines import DatabaseStoreBase
from opennem.schema.network import NetworkWEM
from opennem.utils.dates import parse_date
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class WemStorePulse(DatabaseStoreBase):
    @check_spider_pipeline
    def process_item(self, item, spider=None):

        s = self.session()

        csvreader = csv.DictReader(item["content"].split("\n"))

        records_to_store = []
        primary_keys = []

        for row in csvreader:
            trading_interval = parse_date(
                row["TRADING_DAY_INTERVAL"],
                dayfirst=False,
                network=NetworkWEM,
            )

            if trading_interval not in primary_keys:
                records_to_store.append(
                    {
                        "trading_interval": trading_interval,
                        "network_id": "WEM",
                        "network_region": "WEM",
                        "forecast_load": row["FORECAST_EOI_MW"],
                        # generation_scheduled=row["Scheduled Generation (MW)"],
                        # generation_non_scheduled=row["Non-Scheduled Generation (MW)"],
                        # generation_total=row["Total Generation (MW)"],
                        "price": row["PRICE"],
                    }
                )
                primary_keys.append(trading_interval)

        stmt = insert(BalancingSummary).values(records_to_store)
        stmt.bind = self.engine
        stmt = stmt.on_conflict_do_update(
            constraint="balancing_summary_pkey",
            set_={
                "price": stmt.excluded.price,
                "forecast_load": stmt.excluded.forecast_load,
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
