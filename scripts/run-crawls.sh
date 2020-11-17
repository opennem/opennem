set -euxo pipefail

scrapy crawl -L ERROR au.apvi.current.data

# stats data
scrapy crawl -L ERROR au.wem.live.facility_intervals
scrapy crawl -L ERROR au.wem.live.pulse
scrapy crawl -L ERROR au.wem.current.facility_scada
scrapy crawl -L ERROR au.wem.current.balancing_summary

scrapy crawl -L ERROR au.nem.current.dispatch_scada
scrapy crawl -L ERROR au.nem.current.dispatch
scrapy crawl -L ERROR au.nem.current.dispatch_actual_gen
