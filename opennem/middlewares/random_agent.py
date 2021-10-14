"""
Random user agent for crawler requests. If the spider has the random_user_agent boolean
class property set to true, then this middleware will select a random user agent
for the request.

(c) 2021 OpenNEM - see LICENSE for license details
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from scrapy import Request, Spider, signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware

from opennem.utils.random_agent import get_random_agent

logger = logging.getLogger("opennem.extensions.random_agent")


scrapy_settings = Dict[str, Any]


class RandomUserAgentMiddleware(UserAgentMiddleware):
    """Picks a random user agent for the crawler if it is enabled on the spider"""

    default_user_agent: str

    def __init__(self, settings: scrapy_settings, user_agent: str = "Mozilla/5.0"):
        super(RandomUserAgentMiddleware, self).__init__()
        self.default_user_agent = user_agent
        self.user_agent = user_agent

        ua = settings.get("USER_AGENT", user_agent)

        if ua:
            self.user_agent = self.default_user_agent = ua

        logger.info("Setup {} with user_agent {}".format(self.__class__, self.user_agent))

    @classmethod
    def from_crawler(cls, crawler: Spider) -> RandomUserAgentMiddleware:
        o = cls(settings=crawler.settings, user_agent=crawler.settings["USER_AGENT"])
        crawler.signals.connect(o.spider_opened, signal=signals.spider_opened)
        return o

    def spider_opened(self, spider: Spider) -> None:
        """Custom user agents will in order get local spider setting, random
        agent, settings agent and then default agent"""
        user_agent: Optional[str] = None

        if hasattr(spider, "random_user_agent") and spider.random_user_agent:
            user_agent = get_random_agent()

        user_agent = getattr(spider, "user_agent", user_agent)

        if user_agent:
            self.user_agent = user_agent

    def process_request(self, request: Request, spider: Spider) -> None:
        if self.user_agent:
            logger.info("Setting user agent to: {}".format(self.user_agent))
            request.headers.setdefault(b"User-Agent", self.user_agent)


# debug entry point
if __name__ == "__main__":
    print("Debug entry point for RandomUserAgentMiddleware")
