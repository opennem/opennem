""" """


import logging
from datetime import datetime

from opennem.api.export.tasks import export_energy
from opennem.workers.aggregates import run_aggregates_all_days
from opennem.workers.emissions import run_flow_updates_all_per_year
from opennem.workers.energy import run_energy_update_days

logger = logging.getLogger("opennem.worker.fallback")


def fallback_runner(days: int = 7) -> None:
    run_energy_update_days(days=days)
    run_flow_updates_all_per_year(datetime.now().year, 1)
    run_aggregates_all_days(days=days)
    export_energy(latest=False)


if __name__ == "__main__":
    fallback_runner()
