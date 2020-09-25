# @TODO https://docs.scrapy.org/en/latest/topics/practices.html#run-from-script
# setup scrapy reactor
from huey import RedisHuey, crontab
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor

# from opennem.api.exporter import wem_run_all
from opennem.settings import get_redis_host
from opennem.spiders.nem.scada_dispatch import NemwebCurrentDispatchScada
from opennem.spiders.wem.facilities import WemLiveFacilities
from opennem.spiders.wem.facility_scada import (
    WemCurrentFacilityScada,
    WemLiveFacilityScada,
)
from opennem.spiders.wem.participant import WemParticipantLiveSpider

configure_logging()

settings = get_project_settings()

runner = CrawlerRunner(settings)

REDIS_HOST = get_redis_host()

scheduler = RedisHuey("opennem.scraper", host=REDIS_HOST)


@scheduler.periodic_task(crontab(minute="*/5"))
@defer.inlineCallbacks
def crawl():
    yield runner.crawl(WemParticipantLiveSpider)
    yield runner.crawl(WemLiveFacilities)
    yield runner.crawl(WemLiveFacilityScada)


@scheduler.periodic_task(crontab(minute="*/30"))
@defer.inlineCallbacks
def craw_currents():
    yield runner.crawl(WemCurrentFacilityScada)


@scheduler.periodic_task(crontab(hour="*/2"))
@defer.inlineCallbacks
def craw_nem_currents():
    yield runner.crawl(NemwebCurrentDispatchScada)


@scheduler.periodic_task(crontab(hour="*/2"))
def crawl_historic():
    pass
    # yield runner.crawl()


if __name__ == "__main__":
    reactor.run()
