#!/usr/bin/env python
""" Run all historic crawls, update energy and update seen ranges and other tasks """
import subprocess
import sys
from pathlib import Path

module_dir = Path(__file__).parent.parent

if module_dir not in sys.path:
    sys.path.append(str(module_dir))

for x in sys.path:
    print(x)

from opennem.workers.energy import run_energy_update_all  # noqa: 402
from opennem.workers.facility_data_ranges import update_facility_seen_range  # noqa: 402

ALL_SPIDERS = [
    "au.nem.current.dispatch",
    "au.nem.current.dispatch_actual_gen",
    "au.nem.current.dispatch_is",
    "au.nem.current.dispatch_scada",
    "au.nem.current.rooftop",
    "au.nem.current.rooftop_forecast",
    "au.nem.current.trading_is",
    # archive
    "au.nem.archive.dispatch",
    "au.nem.archive.dispatch_actual_gen",
    "au.nem.archive.dispatch_is",
    "au.nem.archive.dispatch_scada",
    "au.nem.archive.rooftop",
    "au.nem.archive.rooftop_forecast",
    "au.nem.archive.trading_is",
    # mms
    "au.mms.archive.dispatch_price",
    "au.mms.archive.dispatch_regionsum",
    "au.mms.archive.dispatch_scada",
    "au.mms.archive.regionsum",
    "au.mms.archive.rooftop_actual",
    "au.mms.archive.trading_price"
]

exec_poetry = subprocess.run("poetry env info -p", shell=True, capture_output=True, text=True)
env_path = exec_poetry.stdout.strip()

for spider in ALL_SPIDERS:
    print(f"Running crawl {spider}")
    subprocess.run(f"{env_path}/bin/python -m scrapy crawl {spider}", shell=True)

run_energy_update_all()

update_facility_seen_range(True)
