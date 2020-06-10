
from opennem.spiders.wem_base import WemSpider


class NemwebCurrentDispatchScada(WemSpider):
    name = "au.wem.current.facility_scada"
    start_urls = ["http://data.wa.aemo.com.au/datafiles/facility-scada/"]
    limit = 0
