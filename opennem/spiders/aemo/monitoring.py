import logging
from typing import Any, Dict

from pydantic import ValidationError
from scrapy import Spider
from scrapy.http import Response

from opennem.schema.aemo.downloads import AEMOFileDownloadSection
from opennem.utils.dates import parse_date
from opennem.utils.numbers import filesize_from_string
from opennem.utils.url import strip_query_string


class AEMOMonitorRelSpider(Spider):

    name = "au.aemo.downloads"

    start_urls = [
        "https://aemo.com.au/en/energy-systems/electricity/national-electricity-market-nem/participate-in-the-market/registration",
        "https://www.aemo.com.au/energy-systems/electricity/national-electricity-market-nem/nem-forecasting-and-planning/forecasting-and-planning-data/generation-information",
    ]

    pipelines = set([DownloadMonitorPipeline])

    def parse(self, response: Any) -> Dict[str, Any]:

        file_downloads = []

        source_title = response.css("title::text").get()
        download_sections = response.xpath("//div[@class='file-list-wrapper']/..")

        if not download_sections or len(download_sections) < 1:
            raise Exception("{} spider could not find any download sections".format(self.name))

        for download_section in download_sections:
            date_text = download_section.css("div.field-publisheddate span::text").get()

            if not date_text:
                raise Exception(
                    "{} could not get download section published date".format(self.name)
                )

            published_date = parse_date(date_text)

            publish_link_relative = download_section.css("a::attr(href)").get()

            if not publish_link_relative:
                raise Exception("{} could not get rel published link".format(self.name))

            publish_link = response.urljoin(publish_link_relative)

            publish_link = strip_query_string(publish_link)

            download_title = download_section.css(".field-title::text").get()
            download_size_raw = download_section.css(".field-size span::text").get()
            download_size = None

            if download_size_raw:
                download_size, _ = filesize_from_string(download_size_raw)

            # create a model from the extracted fields
            section_model = None

            try:
                section_model = AEMOFileDownloadSection(
                    published_date=published_date,
                    filename=download_title,
                    download_url=publish_link,
                    file_size=download_size,
                    source_url=response.url,
                    source_title=source_title,
                )
                file_downloads.append(section_model)
            except ValidationError as e:
                self.log("Validation error: {}".format(e), logging.ERROR)

        return {"_data": file_downloads, "items": file_downloads}
