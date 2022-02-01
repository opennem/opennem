"""WEM Crawlers"""

import logging

from opennem.clients.wem import (
    get_wem_balancing_summary,
    get_wem_facility_intervals,
    get_wem_live_balancing_summary,
    get_wem_live_facility_intervals,
)
from opennem.controllers.schema import ControllerReturn
from opennem.controllers.wem import store_wem_balancingsummary_set, store_wem_facility_intervals
from opennem.crawlers.schema import CrawlerDefinition

logger = logging.getLogger("opennem.crawlers.wem")


def run_wem_balancing_crawl(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False
) -> ControllerReturn:
    balancing_set = get_wem_balancing_summary()
    cr = store_wem_balancingsummary_set(balancing_set)
    return cr


def run_wem_facility_scada_crawl(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False
) -> ControllerReturn:
    generated_set = get_wem_facility_intervals()
    cr = store_wem_facility_intervals(generated_set)
    return cr


def run_wem_live_balancing_crawl(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False
) -> ControllerReturn:
    balancing_set = get_wem_live_balancing_summary()
    cr = store_wem_balancingsummary_set(balancing_set)
    return cr


def run_wem_live_facility_scada_crawl(
    crawler: CrawlerDefinition, last_crawled: bool = True, limit: bool = False
) -> ControllerReturn:
    generated_set = get_wem_live_facility_intervals()

    cr = store_wem_facility_intervals(generated_set)
    return cr


if __name__ == "__main__":
    pass
