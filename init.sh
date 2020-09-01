# # init db
python -m opennem.db.initdb


python -m opennem.db.load_fixtures

scrapy crawl -L ERROR au.nem.mms.participant
scrapy crawl -L ERROR au.nem.mms.stations

# # scrapy crawl au.nem.mms.stations_status

scrapy crawl -L ERROR au.nem.mms.dudetail_summary
scrapy crawl -L ERROR au.nem.mms.dudetail
scrapy crawl -L ERROR au.nem.mms.statdualloc

scrapy crawl -L DEBUG au.aemo.current.registration_exemption
scrapy crawl -L INFO au.aemo.current.general_information


# # load participants
scrapy crawl -L ERROR au.wem.participant
scrapy crawl -L ERROR au.wem.live.participant

scrapy crawl -L ERROR au.wem.facilities
scrapy crawl -L ERROR au.wem.live.facilities


# # load facilities from wem and nem
scrapy crawl au.aemo.current.registration_exemption
scrapy crawl au.aemo.current.general_information


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

# # map missing fueltechs
python -m opennem.core.facility_fueltechs

# # map missing facilities
python -m opennem.core.load_facilities

# # patches
python -m opennem.core.patches


# # geocode records
python -m opennem.geo.geocode

python -m opennem.exporter.runner

python -m opennem.cli diff
