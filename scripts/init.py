#!/usr/bin/env python
""" Initialization Python Script """
import subprocess

from opennem.api.export.tasks import export_energy, export_power
from opennem.crawl import get_crawl_set, run_crawl
from opennem.exporter.geojson import export_facility_geojson
from opennem.workers.aggregates import run_aggregates_all
from opennem.workers.gap_fill.energy import run_energy_gapfill


def run_crawls() -> None:
    cs = get_crawl_set()

    for crawler in cs.crawlers:
        run_crawl(crawler)


def run_init() -> None:
    pass


def run_exports() -> None:
    run_energy_gapfill(days=30)
    run_aggregates_all()
    export_energy(latest=False)
    export_power(latest=False)


if __name__ == "__main__":
    export_facility_geojson()
    run_crawls()
    run_exports()
