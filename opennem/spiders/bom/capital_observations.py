from opennem.spiders.bom.bom_base import BomJSONObservationSpider


class BomSydneySpider(BomJSONObservationSpider):
    name = "bom.capitals.sydney"
    start_urls = ["http://reg.bom.gov.au/fwo/IDN60901/IDN60901.94767.json"]
    observatory_id = "066037"


class BomMelbourneSpider(BomJSONObservationSpider):
    name = "bom.capitals.melbourne"
    start_urls = ["http://reg.bom.gov.au/fwo/IDV60901/IDV60901.94866.json"]
    observatory_id = "086282"


class BomBrisbaneSpider(BomJSONObservationSpider):
    name = "bom.capitals.brisbane"
    start_urls = ["http://reg.bom.gov.au/fwo/IDQ60901/IDQ60901.94576.json"]
    observatory_id = "040913"


class BomPerthSpider(BomJSONObservationSpider):
    name = "bom.capitals.perth"
    start_urls = ["http://reg.bom.gov.au/fwo/IDW60901/IDW60901.94610.json"]
    observatory_id = "009021"
