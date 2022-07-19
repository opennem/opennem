#!/usr/bin/env python
""" Initialization Python Script """
import subprocess

from opennem.api.export.tasks import export_all_monthly, export_energy, export_power
from opennem.core.crawlers.cli import cmd_crawl_cli
from opennem.core.crawlers.schema import CrawlerSchedule
from opennem.crawl import get_crawl_set, run_crawl
from opennem.db.load_fixtures import load_bom_stations_json, load_fixtures
from opennem.db.tasks import refresh_views
from opennem.db.views import init_aggregation_policies
from opennem.db.views.init import init_views_cli
from opennem.exporter.geojson import export_facility_geojson
from opennem.importer.all import run_all
from opennem.importer.db import import_facilities
from opennem.importer.db import init as db_init
from opennem.importer.emissions import import_emissions_map
from opennem.importer.interconnectors import import_nem_interconnects
from opennem.importer.mms import mms_export
from opennem.importer.opennem import opennem_import
from opennem.settings import settings
from opennem.workers.aggregates import run_aggregate_days, run_aggregates_all
from opennem.workers.energy import run_energy_update_archive, run_energy_update_days
from opennem.workers.gap_fill.energy import run_energy_gapfill
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


def run_init() -> None:
    db_init()
    export_facility_geojson()
    run_crawls()
    run_network_data_range_update()
    run_exports()


def run_exports() -> None:
    run_energy_gapfill(days=30)
    run_aggregates_all()
    export_energy(latest=False)
    export_power(latest=False)


if __name__ == "__main__":
    run_init()
