set -euxo pipefail

# alembic upgrade head

# python -m opennem.cli db init

scrapy crawl -L ERROR au.wem.participant
scrapy crawl -L ERROR au.wem.live.participant

scrapy crawl -L ERROR au.wem.facilities
scrapy crawl -L ERROR au.wem.live.facilities

# bom data
scrapy crawl -L ERROR bom.capitals

# rooftop
scrapy crawl -L ERROR au.apvi.current.data

# stats data
scrapy crawl -L ERROR au.wem.live.facility_intervals
scrapy crawl -L ERROR au.wem.current.facility_scada
scrapy crawl -L ERROR au.wem.current.balancing_summary
scrapy crawl -L ERROR au.nem.current.dispatch_scada
scrapy crawl -L ERROR au.nem.current.dispatch
scrapy crawl -L ERROR au.nem.current.dispatch_actual_gen

python -m opennem.importer.wikidata
