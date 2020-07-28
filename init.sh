# # init db
python -m opennem.db.initdb

# # load required fixtures
python -m opennem.db.load_fixtures
python -m opennem.db.load_facilitymap


# # load participants
scrapy crawl -L ERROR au.wem.participant
scrapy crawl -L ERROR au.wem.live.participant

# # load facilities from wem and nem
scrapy crawl -L INFO au.nem.facilities.rel
scrapy crawl -L INFO au.nem.facilities.gi

scrapy crawl -L ERROR au.wem.facilities
scrapy crawl -L ERROR au.wem.live.facilities


# # merge with current facility mapping data (will import nem)
# # python db_test.py

# # bom data
# # scrapy crawl -L ERROR bom.capitals.perth
# # scrapy crawl -L ERROR bom.capitals.sydney
# # scrapy crawl -L ERROR bom.capitals.melbourne
# # scrapy crawl -L ERROR bom.capitals.brisbane

# # wem current data
# # scrapy crawl -L ERROR au.wem.current.balancing_summary
# # scrapy crawl -L ERROR au.wem.current.facility_scada

# # wem archive data
# # scrapy crawl -L ERROR au.wem.archive.balancing_summary
# # scrapy crawl -L ERROR au.wem.archive.facility_scada

# # nem current data
# # scrapy crawl au.nem.current.dispatch_is
# # scrapy crawl au.nem.current.dispatch_scada

# # nem archive data
# # scrapy crawl au.nem.archive.dispatch_is
# # scrapy crawl au.nem.archive.dispatch_scada

# # python -m opennem.api.exporter
# #

# python -m opennem.geo.geocode

python -m opennem.core.patches

python -m opennem.geo.export

python facility_diff.py
