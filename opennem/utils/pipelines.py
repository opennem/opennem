import functools
import logging
from typing import Any, Callable, Dict

from scrapy.spiders import Spider


def check_spider_pipeline(process_item_method: Callable) -> Callable:
    @functools.wraps(process_item_method)
    def wrapper(self, item: Dict, spider: Spider) -> Any:  # type: ignore

        # message template for debugging
        msg = "%%s %s pipeline step" % (self.__class__.__name__,)

        pipelines = set([])

        if hasattr(spider, "pipelines"):
            if type(spider.pipelines) is set:
                pipelines |= spider.pipelines

        if hasattr(spider, "pipelines_extra"):
            if type(spider.pipelines_extra) is set:
                pipelines |= spider.pipelines_extra

        if self.__class__ in pipelines:
            spider.log(msg % "Executing", level=logging.INFO)
            return process_item_method(self, item, spider)

        else:
            # spider.log(msg % "skipping", level=logging.DEBUG)
            return item

    return wrapper
