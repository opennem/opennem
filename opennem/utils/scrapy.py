from typing import List

from scrapy import spiderloader
from scrapy.utils import project


def get_spiders() -> List[str]:
    """
    Get a list of spiders from scrapy

    """
    scrapy_settings = project.get_project_settings()
    spider_loader = spiderloader.SpiderLoader.from_settings(scrapy_settings)
    spiders = spider_loader.list()
    classes = [spider_loader.load(name) for name in spiders]

    return [str(i.name) for i in classes]
