#!/usr/bin/env python
""" Initialization Python Script """
import subprocess

from opennem import settings
from opennem.api.export.tasks import export_energy, export_power
from opennem.core.crawlers.schema import CrawlerSchedule
from opennem.crawl import get_crawl_set, run_crawl
from opennem.db.load_fixtures import load_fixtures
from opennem.exporter.geojson import export_facility_geojson
from opennem.importer.db import import_facilities
from opennem.importer.db import init as db_init
from opennem.importer.interconnectors import import_nem_interconnects
from opennem.importer.opennem import opennem_import
from opennem.workers.daily import all_runner
from opennem.workers.facility_data_ranges import update_facility_seen_range
from opennem.workers.network_data_range import run_network_data_range_update


def run_crawls() -> None:
    cs = get_crawl_set()

    for crawler in cs.crawlers:
        if crawler.schedule and crawler.schedule == CrawlerSchedule.live:
            run_crawl(crawler)


def init_db() -> None:
    subprocess.run(["alembic", "upgrade", "head"])
    db_init()
    load_fixtures()
    opennem_import()
    import_facilities()
    import_nem_interconnects()


def run_exports() -> None:
    all_runner()
    export_energy(latest=False)
    export_power(latest=False)


def run_init() -> None:
    db_init()
    export_facility_geojson()
    run_crawls()
    run_network_data_range_update()
    update_facility_seen_range(include_first_seen=True)
    run_exports()


if __name__ == "__main__":
    run_init()
