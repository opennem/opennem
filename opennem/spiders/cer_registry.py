from scrapy import Spider


class CERRegistrySpider(Spider):
    # name = "au.cer.registry"
    start_urls = [
        "https://www.rec-registry.gov.au/rec-registry/app/public/power-station-register"
    ]
