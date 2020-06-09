
from opennem.spiders.nemweb import NemwebSpider


class NemwebCurrentDispatchScada(NemwebSpider):
    name = "au.nem.current.dispatch_scada"
    start_urls = ["http://www.nemweb.com.au/Reports/CURRENT/Dispatch_SCADA/"]
    limit = 1
