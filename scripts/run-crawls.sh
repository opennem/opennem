set -euxo pipefail

# apvi
scrapy crawl -L ERROR au.apvi.current.data

# stats data wem
scrapy crawl -L ERROR au.wem.live.facility_intervals
scrapy crawl -L ERROR au.wem.live.pulse
scrapy crawl -L ERROR au.wem.current.facility_scada
scrapy crawl -L ERROR au.wem.current.balancing_summary

# nem
scrapy crawl -L ERROR au.nem.current.dispatch_scada
scrapy crawl -L ERROR au.nem.current.dispatch
scrapy crawl -L ERROR au.nem.current.dispatch_actual_gen
scrapy crawl -L ERROR au.nem.current.rooftop


# bom
scrapy crawl bom.all
scrapy crawl bom.capitals
