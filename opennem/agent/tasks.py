"""
    Scrapy Crawl Scheduler

    @TODO implement a custom reactor and runner

"""
from huey import RedisHuey, crontab
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import defer

from opennem.settings import settings
from opennem.spiders.bom.capital_observations import (
    BomAllSpider,
    BomCapitalsSpider,
)
from opennem.spiders.nem.dispatch import NemwebCurrentDispatch
from opennem.spiders.nem.price import (
    NemwebCurrentPriceSpider,
    NemwebLatestPriceSpider,
)
from opennem.spiders.nem.scada_dispatch import (
    NemwebCurrentDispatchScada,
    NemwebLatestDispatchScada,
)
from opennem.spiders.wem.facilities import WemLiveFacilities
from opennem.spiders.wem.facility_scada import (
    WemCurrentFacilityScada,
    WemLiveFacilityScada,
)
from opennem.spiders.wem.participant import WemParticipantLiveSpider

configure_logging()

scrapy_settings = get_project_settings()

# override settings
scrapy_settings["LOG_LEVEL"] = "ERROR"

scheduler = RedisHuey("opennem.scraper", host=settings.cache_url.host)

runner = CrawlerProcess(scrapy_settings)


@scheduler.periodic_task(crontab(minute="*/1"))
@defer.inlineCallbacks
def every_minute():
    # runner = CrawlerProcess(scrapy_settings)
    yield runner.crawl(NemwebLatestPriceSpider)
    yield runner.crawl(NemwebLatestDispatchScada)
    # runner.start()


@scheduler.periodic_task(crontab(minute="*/5"))
@defer.inlineCallbacks
def every_five():
    yield runner.crawl(BomCapitalsSpider)


@scheduler.periodic_task(crontab(minute="*/10"))
def every_ten():
    runner = CrawlerProcess(scrapy_settings)
    runner.crawl(WemParticipantLiveSpider)
    runner.crawl(WemLiveFacilities)
    runner.crawl(WemLiveFacilityScada)
    runner.start()


@scheduler.periodic_task(crontab(minute="*/15"))
def every_fifeteen():
    runner = CrawlerProcess(scrapy_settings)
    runner.crawl(BomAllSpider)
    runner.start()


@scheduler.periodic_task(crontab(minute="*/30"))
def every_thirty():
    runner = CrawlerProcess(scrapy_settings)
    runner.crawl(WemCurrentFacilityScada)
    runner.start()


@scheduler.periodic_task(crontab(hour="*/1"))
def every_hour():
    runner = CrawlerProcess(scrapy_settings)
    runner.crawl(NemwebCurrentDispatchScada)
    runner.crawl(NemwebCurrentPriceSpider)
    runner.start()


# At 6pm UTC start looking for next day dispatches
@scheduler.periodic_task(crontab(hour="18-20"))
# @defer.inlineCallbacks
def crawl_dispatch_dailies():
    runner.crawl(NemwebCurrentDispatch)
    runner.start()


@scheduler.task()
def run_onstartup():
    runner = CrawlerProcess(scrapy_settings)
    runner.start(stop_after_crawl=False)


runner.start(stop_after_crawl=False)
