"""
Client to monitor files available on the AEMO website

 * extracts general information updates
 * extracts participant files
 * gets all other available files and can notify on updates
"""

import logging

from bs4 import BeautifulSoup
from pydantic import ValidationError

from opennem.core.downloader import url_downloader
from opennem.schema.aemo.downloads import AEMOFileDownloadSection
from opennem.utils.dates import parse_date
from opennem.utils.numbers import filesize_from_string
from opennem.utils.url import strip_query_string

logger = logging.getLogger("opennem.clients.aemo_monitor")

REG_URL = (
    "https://aemo.com.au/en/energy-systems/electricity/national-electricity-market-nem/participate-in-the-market/registration"
)
FORECAST_URL = (
    "https://www.aemo.com.au/energy-systems/electricity/"
    "national-electricity-market-nem/nem-forecasting-and-planning/forecasting-and-planning-data/generation-information",
)


def monitor_aemo_station_info() -> list[AEMOFileDownloadSection]:
    start_urls = [REG_URL, FORECAST_URL]

    file_downloads = []

    downloaded_content = url_downloader(start_urls[0])

    response = BeautifulSoup(downloaded_content.decode("utf-8"))

    source_title = response.css("title::text").get()
    download_sections = response.xpath("//div[@class='file-list-wrapper']/..")

    if not download_sections or len(download_sections) < 1:
        raise Exception("AEMO monitoring crawler could not find any download sections")

    for download_section in download_sections:
        date_text = download_section.css("div.field-publisheddate span::text").get()

        if not date_text:
            raise Exception("AEMO website monitor could not get download section published date")

        published_date = parse_date(date_text)

        publish_link_relative = download_section.css("a::attr(href)").get()

        if not publish_link_relative:
            raise Exception("AEMO website monitor could not get rel published link")

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
            logger.error(f"Validation error: {e}", logging.ERROR)

    return file_downloads
