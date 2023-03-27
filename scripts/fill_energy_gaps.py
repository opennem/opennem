#!/usr/bin/env python
""" Fill energy gaps

A bug in workers.energy deleted energies in facility_scada for the

Jun-2013 -> Dec-2017 period

This worker will fill them using multiprocessing to speed up the process
"""
import logging
from datetime import datetime, timedelta
from multiprocessing import Pool

from dateutil.relativedelta import relativedelta

from opennem.schema.network import NetworkNEM
from opennem.workers.energy import run_energy_calc

logger = logging.getLogger("opennem.fill_energy_gaps")


def fill_energy_gaps_for_month(date_month: datetime) -> None:
    """This fills the energy gaps for a year with multiprocessing"""
    date_min = date_month.replace(day=1, hour=0, second=0, minute=0, microsecond=0)
    date_max = date_min + relativedelta(months=1)

    # logging.info("Running for ")
    run_energy_calc(date_min=date_min, date_max=date_max, network=NetworkNEM)


def fill_energy_gaps_for_day(date_day: datetime) -> None:
    """This fills the energy gaps for a year with multiprocessing"""
    date_min = date_day.replace(hour=0, second=0, minute=0, microsecond=0)
    date_max = date_min + timedelta(days=1)

    # logging.info("Running for ")
    run_energy_calc(date_min=date_min, date_max=date_max, network=NetworkNEM)


def run_fill_months(date_start: datetime, num_months: int = 12) -> None:
    with Pool(processes=4) as pool:
        for i in range(num_months):
            date_month = date_start + relativedelta(months=i)
            pool.apply_async(fill_energy_gaps_for_month, (date_month,))

        pool.close()
        pool.join()


def run_fill_days(date_start: datetime, date_end: datetime) -> None:
    num_days = (date_end - date_start).days

    with Pool(processes=6) as pool:
        for i in range(num_days + 1):
            date_day = date_start + timedelta(days=i)
            pool.apply_async(fill_energy_gaps_for_day, (date_day,))

        pool.close()
        pool.join()


if __name__ == "__main__":
    run_fill_days(
        date_start=datetime.fromisoformat("2013-06-01T00:00:00+10:00"),
        date_end=datetime.fromisoformat("2018-01-01T00:00:00+10:00"),
        # date_end=datetime.fromisoformat("2017-07-31T00:00:00+10:00"),
    )
    # run_fill_days(
    #     date_start=datetime.fromisoformat("2017-01-01T00:00:00+10:00"),
    #     date_end=datetime.fromisoformat("2018-01-01T00:00:00+10:00"),
    #     # date_end=datetime.fromisoformat("2017-07-31T00:00:00+10:00"),
    # )
