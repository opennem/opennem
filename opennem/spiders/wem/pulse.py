from opennem.pipelines.wem.pulse import WemStorePulse
from opennem.spiders.wem import WemCurrentSpider


class WemPulseCurrentSpider(WemCurrentSpider):
    name = "au.wem.live.pulse"
    pipelines_extra = set([WemStorePulse])

    start_url = (
        "https://aemo.com.au/aemo/data/wa/infographic/neartime/pulse.csv"
    )
