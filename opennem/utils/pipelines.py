import functools
import logging
import re

import six


def regex(x):
    if isinstance(x, six.string_types):
        return re.compile(x)
    return x


def check_spider_pipeline(process_item_method):
    @functools.wraps(process_item_method)
    def wrapper(self, item, spider):

        # message template for debugging
        msg = "%%s %s pipeline step" % (self.__class__.__name__,)

        if not hasattr(spider, "pipelines"):
            spider.pipelines = set()

        if self.__class__ in spider.pipelines:
            spider.log(msg % "executing", level=logging.DEBUG)
            return process_item_method(self, item, spider)

        else:
            spider.log(msg % "skipping", level=logging.DEBUG)
            return item

    return wrapper
