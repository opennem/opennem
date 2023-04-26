"""WEM Crawlers"""

import logging

from opennem.clients.wem import (
    get_wem_balancing_summary,
    get_wem_facility_intervals,
    get_wem_live_balancing_summary,
    get_wem_live_facility_intervals,
)
from opennem.controllers.schema import ControllerReturn
from opennem.controllers.wem import (
    store_wem_balancingsummary_set,
    store_wem_facility_intervals,
    store_wem_facility_intervals_bulk,
)
from opennem.core.crawlers.schema import CrawlerDefinition, CrawlerPriority, CrawlerSchedule

logger = logging.getLogger("opennem.crawlers.wem")


def run_wem_balancing_crawl(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False, latest: bool = False
) -> ControllerReturn:
    balancing_set = get_wem_balancing_summary()
    cr = store_wem_balancingsummary_set(balancing_set)
    return cr


def run_wem_facility_scada_crawl(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False, latest: bool = False
) -> ControllerReturn:
    generated_set = get_wem_facility_intervals()
    cr = store_wem_facility_intervals(generated_set)
    return cr


def run_wem_live_balancing_crawl(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False, latest: bool = False
) -> ControllerReturn:
    balancing_set = get_wem_live_balancing_summary()
    cr = store_wem_balancingsummary_set(balancing_set)
    return cr


def run_wem_live_facility_scada_crawl(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False, latest: bool = False
) -> ControllerReturn:
    generated_set = get_wem_live_facility_intervals(trim_intervals=True)

    cr = store_wem_facility_intervals_bulk(generated_set)
    return cr


WEMBalancing = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.hourly,
    name="au.wem.balancing",
    processor=run_wem_balancing_crawl,
)

WEMFacilityScada = CrawlerDefinition(
    priority=CrawlerPriority.medium,
    schedule=CrawlerSchedule.hourly,
    name="au.wem.facility_scada",
    processor=run_wem_facility_scada_crawl,
)

WEMBalancingLive = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.frequent,
    name="au.wem.live.balancing",
    processor=run_wem_live_balancing_crawl,
)

WEMFacilityScadaLive = CrawlerDefinition(
    priority=CrawlerPriority.high,
    schedule=CrawlerSchedule.frequent,
    name="au.wem.live.facility_scada",
    processor=run_wem_live_facility_scada_crawl,
)

if __name__ == "__main__":
    pass
