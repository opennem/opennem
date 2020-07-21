import scrapy

from opennem.spiders.dirlisting import DirlistingSpider


class NemArchiveMMSSpider(DirlistingSpider):
    name = "au.nem.archive.mms"

    start_urls = [
        "http://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/2020/MMSDM_2020_06/MMSDM_Historical_Data_SQLLoader/DATA/"
    ]
