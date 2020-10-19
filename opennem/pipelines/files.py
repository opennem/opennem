import logging
import os

from requests import RequestException

from opennem.utils.handlers import open
from opennem.utils.pipelines import check_spider_pipeline

logger = logging.getLogger(__name__)


class LinkExtract(object):
    """
        parses and extracts links in items

    """

    @check_spider_pipeline
    def process_item(self, item, spider):
        if "link" not in item:
            return item

        url = item["link"]
        fh = None
        content = None
        _, file_extension = os.path.splitext(url)

        try:
            fh = open(url)
        except RequestException:
            logger.error("Bad link: {}".format(url))
        except Exception as e:
            logger.error("Error: {}".format(e))

        if fh:
            content = fh.read()

            item["content"] = content
            item["extension"] = file_extension

        return item
