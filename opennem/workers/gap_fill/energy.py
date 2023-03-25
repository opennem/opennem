"""OpenNEM Gapfill
"""

import logging
from datetime import datetime, timedelta
from textwrap import dedent

from datetime_truncate import truncate as date_trunc

from opennem import settings
from opennem.core.networks import network_from_network_code
from opennem.db import get_database_engine
from opennem.schema.core import BaseConfig
from opennem.schema.network import NetworkAEMORooftop, NetworkAPVI, NetworkNEM, NetworkSchema, NetworkWEM
from opennem.utils.dates import get_last_complete_day_for_network, get_today_nem
from opennem.utils.timezone import is_aware
from opennem.workers.energy import run_energy_calc

logger = logging.getLogger("opennem.workers.gap_fill")


class GapFillEnergyException(Exception):
    pass


class EnergyGap(BaseConfig):
    interval: datetime
    network_id: str
    has_power: bool
    has_energy: bool
    total_generated: float | None
    total_energy: float | None


def query_energy_gaps(date_min: datetime, date_max: datetime, network: NetworkSchema = NetworkNEM) -> list[EnergyGap]:
    """Query gaps in energy and power. Minimum date is inclusive, maximum date is exclusive"""

    engine = get_database_engine()

    __query = """

        select
            t.interval at time zone '{tz}' as interval,
            t.network_id,
            t.has_power,
            t.has_energy,
            t.total_generated,
            t.total_energy
        from (
            select
                time_bucket_gapfill('1 hour', fs.trading_interval ) as interval,
                fs.network_id,
                case when sum(fs.generated) is NULL then FALSE else TRUE end as has_power,
                case when sum(fs.eoi_quantity) IS NULL then FALSE else TRUE end as has_energy,
                sum(fs.generated) as total_generated,
                sum(fs.eoi_quantity) as total_energy
            from facility_scada fs
            join facility f on fs.facility_code = f.code
            where
                fs.trading_interval >= '{date_min}'
                and fs.trading_interval < '{date_max}'
                and fs.network_id='{network_id}'
            group by 1, fs.network_id
        ) as t
        where
            t.has_power is TRUE
            order by t.interval desc;

    """

    results = []

    # Set the timezone on dates if they haven't been already
    for dt in {date_min, date_max}:
        if not is_aware(dt):
            dt = dt.replace(tzinfo=network.get_fixed_offset())

    # Truncate dates down to each hour
    # @NOTE we can make this a parm and adjust both the bucket size and the trunc
    for dt in {date_min, date_max}:
        dt = date_trunc(dt, "hour")

    query = __query.format(tz=network.timezone_database, date_min=date_min, date_max=date_max, network_id=network.code)

    logger.debug(dedent(query))

    with engine.begin() as c:
        results = c.execute(query)

    return [EnergyGap(**i) for i in results]


def run_energy_gapfill(
    date_min: datetime, date_max: datetime, network: NetworkSchema, fill_all: bool = False, fill_gaps: bool = True
) -> list[EnergyGap]:
    """ """
    energy_gaps = query_energy_gaps(date_min=date_min, date_max=date_max, network=network)

    energy_gaps_filtered = list(filter(lambda x: x.has_power is True and x.has_energy is False, energy_gaps))

    if fill_all:
        energy_gaps_filtered = energy_gaps

    logger.info(f"Found {len(energy_gaps_filtered)} energy gaps interval hours")

    if not fill_gaps:
        return energy_gaps

    for gap in energy_gaps_filtered:
        logger.info(
            f"{gap.network_id} Running for interval {gap.interval} with power: {gap.has_power} \
                energy: {gap.has_energy} energy_value: {gap.total_energy}"
        )

        if settings.dry_run:
            continue

        dmin = gap.interval
        dmax = dmin + timedelta(hours=1)

        try:
            run_energy_calc(dmin, dmax, network=network_from_network_code(gap.network_id))
        except Exception:
            logger.error(f"Error running {gap.network_id} energy gapfill for {dmin} => {dmax}")

    return energy_gaps_filtered


def run_energy_gapfill_for_network_by_days(
    network: NetworkSchema = NetworkNEM, days: int = 7, fill_all: bool = False, fill_gaps: bool = True
) -> None:
    """Run energy gapfilling. If fill all it will ignore if it has energy. If fill gaps it will only fill gaps"""

    # calculate
    date_max = get_last_complete_day_for_network(network)
    date_min = date_max - timedelta(days=days)

    run_energy_gapfill(date_min, date_max=date_max, network=network, fill_all=fill_all, fill_gaps=fill_gaps)


def run_energy_gapfill_for_network(network: NetworkSchema) -> None:
    """Run energy gapfille for a network by year"""

    if not network or not network.data_first_seen:
        raise GapFillEnergyException("Require network date first seen to run")

    current_year = datetime.now().year

    for year in range(current_year, network.data_first_seen.year - 1, -1):
        date_start = datetime(year=year, month=1, day=1, hour=0, minute=0, second=0, tzinfo=network.get_fixed_offset())
        date_end = date_start.replace(year=year + 1)

        if year == current_year:
            date_end = date_trunc(get_today_nem(), "hour")

        if year == network.data_first_seen.year:
            date_start = date_trunc(network.data_first_seen, "hour") + timedelta(hours=1)

        logging.info(f"Running for {date_start} => {date_end}")

        run_energy_gapfill(date_min=date_start, date_max=date_end, network=network, fill_all=False, fill_gaps=True)


def run_energy_gapfill_previous_days(days: int = 14, networks: list[NetworkSchema] = None, run_all: bool = False) -> None:
    """Run gapfill of energy values - will find gaps in energy values and run energy_sum"""
    if networks is None:
        networks = [NetworkNEM, NetworkWEM, NetworkAPVI, NetworkAEMORooftop]

    for network in networks:
        logger.info(f"Running energy gapfill for {network.code}")

        try:
            run_energy_gapfill_for_network_by_days(network, days=days, fill_all=run_all)
        except Exception as e:
            logger.error(f"gap_fill run error: {e}")


def run_energy_gapfill_for_last_hour(network: NetworkSchema) -> None:
    """Run energy gapfill for the last hour"""

    date_max = date_trunc(get_today_nem(), "hour")
    date_min = date_max - timedelta(hours=1)

    run_energy_gapfill(date_min, date_max=date_max, network=network, fill_all=False, fill_gaps=True)


# debug entry point
if __name__ == "__main__":
    # run_energy_gapfill(days=365/2)
    # dmin = datetime.fromisoformat("2022-02-28T00:00:00+10:00")
    # dmax = dmin + timedelta(days=3)
    # run_energy_calc(dmin, dmax, network=network_from_network_code("NEM"))

    # energy_intervals = query_energy_gaps(network=network_from_network_code("NEM"), days=301)
    # energy_gaps = list(filter(lambda x: x.has_energy is False, energy_intervals))

    run_energy_gapfill_for_network(NetworkNEM)

    # energy_gaps = run_energy_gapfill_for_network_by_days(network=NetworkNEM, fill_gaps=False)

    # print(f"{len(energy_gaps)} gaps")

    # for i in energy_gaps:
    #     print(i.interval, i.has_power, i.has_energy, i.total_energy)
