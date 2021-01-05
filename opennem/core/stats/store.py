"""
Methods to store and persist stats in the database or to JSON
"""
import logging

from sqlalchemy.dialects.postgresql import insert

from opennem.core.loader import get_data_path
from opennem.core.parsers.cpi import stat_au_cpi
from opennem.db import SessionLocal, get_database_engine
from opennem.db.models.opennem import Stats
from opennem.schema.stats import StatsSet

logger = logging.getLogger("opennem.stats.store")


def store_stats_database(statset: StatsSet) -> int:
    s = SessionLocal()

    records_to_store = [i.dict() for i in statset.stats]

    stmt = insert(Stats).values(records_to_store)
    stmt.bind = get_database_engine()
    stmt = stmt.on_conflict_do_update(
        index_elements=[
            "stat_date",
            "country",
            "stat_type",
        ],
        set_={
            "value": stmt.excluded.value,
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

    num_records = len(records_to_store)

    logger.info("Wrote {} records to database".format(num_records))

    return num_records


def store_stats_json(records_to_store: StatsSet) -> bool:
    data_dir = get_data_path()

    with open(data_dir / "au_cpi.json", "w") as fh:
        fh.write(records_to_store.json(indent=4))

    logger.info("Wrote stat set json to {}".format(data_dir / "au_cpi.json"))

    return True


if __name__ == "__main__":
    r = stat_au_cpi()
    store_stats_database(r)
