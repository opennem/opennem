"""
OpenNEM AEMO Downloads monitoring pipeline

Tracks AEMO downloads and monitors them
"""

import logging
from typing import Any, List

from scrapy import Spider

from opennem.schema.aemo.downloads import AEMOFileDownloadSection
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger("opennem.pipelines.meta")


class DownloadMonitorPipeline(object):
    """
    Gets a list of all available AEMO downloads and checks for new files

    If the pipeline item has a "link" it'll download the content
    and attach it to the item as "content" along with some
    basic metadata.

    """

    @check_spider_pipeline
    def process_item(self, item: Any, spider: Spider) -> None:
        if "items" not in item:
            logger.error("No items to {}".format(self.__class__))
            return None

        file_downloads: List[AEMOFileDownloadSection] = item["items"]

        for dl in file_downloads:
            print(
                "Date: {}\nFile: {}\nSource: {}\nDownload: {}\n************\n".format(
                    dl.published_date, dl.filename, dl.source_url, dl.download_url
                )
            )

        return item
