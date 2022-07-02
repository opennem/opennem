#!/usr/bin/env python
"""
Scratchpad to export JSON's for unit tests + testing
"""

from opennem.api.export.map import PriorityType, StatType, get_export_map, get_weekly_export_map
from opennem.api.export.tasks import export_electricitymap, export_energy, export_power
from opennem.api.stats.controllers import get_scada_range
from opennem.controllers.nem import ControllerReturn, store_aemo_tableset
from opennem.core.compat.loader import get_dataset
from opennem.core.crawlers.history import (
    CrawlHistoryEntry,
    get_crawler_history,
    get_crawler_missing_intervals,
    set_crawler_history,
)
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule
from opennem.core.parsers.aemo.mms import parse_aemo_url, parse_aemo_urls
from opennem.core.parsers.dirlisting import get_dirlisting
from opennem.crawl import get_crawl_set, run_crawl
from opennem.schema.network import NetworkAEMORooftop, NetworkAPVI, NetworkNEM, NetworkWEM
from opennem.workers.aggregates import run_aggregates_all, run_aggregates_all_days
from opennem.workers.gap_fill.energy import run_energy_gapfill


def run_tests() -> None:
    export_map = get_export_map()

    power = (
        export_map.get_by_network_id("NEM")
        .get_by_stat_type(StatType.power)
        .get_by_network_region("SA1")
        # .get_by_priority(PriorityType.history)
        .get_by_priority(PriorityType.live)
    )

    export_power(power.resources)
    return None

    # print(power.resources)

    # energy_map = (
    #     export_map.get_by_network_id("NEM")
    #     .get_by_network_region("SA1")
    #     .get_by_stat_type(StatType.energy)
    #     .get_by_priority(PriorityType.monthly)
    #     # .get_by_years([2022])
    # )

    # if len(energy_map.resources):
    #     export_energy(energy_map.resources)

    # return None

    energy_map = (
        export_map.get_by_priority(PriorityType.daily)
        .get_by_stat_type(StatType.energy)
        .get_by_network_id("WEM")
        # .get_by_network_region("NSW1")
        # .get_by_years([2021])
    )

    for r in energy_map.resources:
        print(
            "Exporting: {} {} {}: {} => {}".format(
                r.year, r.network.code, r.network_region, r.date_range.start, r.date_range.end
            )
        )
        export_energy([r])

    # if len(energy_map.resources):
    #     print(
    #         export_map.resources[0].network.code,
    #         [i.code for i in export_map.resources[0].networks],
    #     )
    #     export_energy(energy_map.resources)


def load_flows() -> None:
    pass


def fallback_runner(days: int = 7) -> None:
    run_energy_update_days(days=days)
    run_aggregates_all_days(days=days)
    export_energy(latest=False)


from opennem.workers.energy import run_energy_calc, run_energy_update_all, run_energy_update_days


def test_parser() -> None:
    urls = [
        "https://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_202206250930_0000000365801254.zip",
        "https://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_202206250935_0000000365801429.zip",
        "https://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_202206250940_0000000365801640.zip",
        "https://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/PUBLIC_DISPATCHSCADA_202206250945_0000000365801797.zip",
    ]

    r = parse_aemo_urls(urls)
    assert r.has_table("unit_scada"), "has table"

    print("has table and done")

    controller_returns = store_aemo_tableset(r)
    print(controller_returns)


#
if __name__ == "__main__":
    # run_tests()
    # cs = get_crawl_set()

    # run_crawl(cs.get_crawler("au.nem.archive.dispatch_scada"))
    # run_crawl(cs.get_crawler("au.nem.catchup.dispatch_actual_gen"))
    # run_crawl(cs.get_crawler("au.nem.catchup.dispatch"))

    # run_energy_gapfill(days=30)
    # run_aggregates_all()
    # export_energy(latest=False)
    # test_parser()
    # export_power()
    fallback_runner()
    # dmin = datetime.fromisoformat("2022-02-17 07:00:00+08:00")
    # dmax = dmin + timedelta(hours=1)
    # export_energy(latest=True)
    # run_energy_calc(dmin, dmax, network=NetworkWEM)
