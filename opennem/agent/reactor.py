# @TODO https://docs.scrapy.org/en/latest/topics/practices.html#run-from-script
# setup scrapy reactor
from huey import RedisHuey, crontab
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.internet import defer, reactor

# from opennem.api.exporter import wem_run_all
from opennem.settings import get_redis_host
from opennem.spiders.wem.participant import WemParticipantLiveSpider

configure_logging()

settings = get_project_settings()

runner = CrawlerRunner(settings)

REDIS_HOST = get_redis_host()

scheduler = RedisHuey("opennem.scraper", host=REDIS_HOST)


@scheduler.periodic_task(crontab(minute="*/1"))
@defer.inlineCallbacks
def crawl():
    yield runner.crawl(WemParticipantLiveSpider)
    # yield runner.crawl(MySpider2)
    # reactor.stop()


if __name__ == "__main__":
    reactor.run()
