from opennem.pipelines.wem.participant import (
    WemStoreLiveParticipant,
    WemStoreParticipant,
)
from opennem.spiders.wem import WemCurrentSpider


class WemParticipantSpider(WemCurrentSpider):
    name = "au.wem.participant"

    pipelines_extra = set([WemStoreParticipant,])

    start_url = "http://data.wa.aemo.com.au/public/public-data/datafiles/participants/participants.csv"


class WemParticipantLiveSpider(WemCurrentSpider):
    name = "au.wem.live.participant"

    pipelines_extra = set([WemStoreLiveParticipant,])

    start_url = "https://aemo.com.au/aemo/data/wa/infographic/participant.csv"
