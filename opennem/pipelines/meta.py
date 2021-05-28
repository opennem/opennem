"""
OpenNEM Meta Pipelines

Attach info before/after spider runs
"""

import logging
from typing import Any

from scrapy import Spider

from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger("opennem.pipelines.meta")


class MetaPrePipeline(object):
    """
    Parse and extracts links in items.

    If the pipeline item has a "link" it'll download the content
    and attach it to the item as "content" along with some
    basic metadata.

    """

    @check_spider_pipeline
    def process_item(self, item: Any, spider: Spider) -> None:
        logger.info("meta post pipeline")


class MetaPostPipeline(object):
    """
    Parse and extracts links in items.

    If the pipeline item has a "link" it'll download the content
    and attach it to the item as "content" along with some
    basic metadata.

    """

    @check_spider_pipeline
    def process_item(self, item: Any, spider: Spider) -> None:
        logger.info("meta post pipeline")
