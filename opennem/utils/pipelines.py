"""
OpenNEM Spider Pipeline Module


This is a custom module for scrapy that allows you to set custom pipelines
to execute. By default scrapy will pass a crawler through every pipeline
step.

The pipelines you want to execute should be included as a set. You can
set them using the pipelines or pipelines_extra class property on the
spider.

ex.

In [9]: class ExampleSpider(Spider):
   ...:     name = "spider.test"
   ...:     pipelines = set([LinkExtract])
   ...:

The pipelines process_item method need to be wrapped in check_spider_pipeline

ex.

```
In [6]: class NemwebUnitScadaOpenNEMStorePipeline(object):
   ...:     @check_spider_pipeline
   ...:     def process_item(self, item: Dict[str, Any], spider=None) -> List:
   ...:         pass
   ...:
```

With no wrapping it will execute the pipeline per normal scrapy behavior.
"""

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
