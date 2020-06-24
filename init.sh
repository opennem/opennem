# init db
python -m opennem.db.initdb

# load required fixtures
python -m opennem.db.load_fixtures

# load facilities from wem and nem
scrapy crawl au.wem.facilities

# merge with current facility mapping data (will import nem)
python db_test.py

# bom data
scrapy crawl bom.capitals.perth
scrapy crawl bom.capitals.sydney
scrapy crawl bom.capitals.melbourne
scrapy crawl bom.capitals.brisbane

# wem current data
scrapy crawl au.wem.current.balancing_summary
scrapy crawl au.wem.current.facility_scada

# wem archive data
scrapy crawl au.wem.archive.balancing_summary
scrapy crawl au.wem.archive.facility_scada

# nem current data
scrapy crawl au.nem.current.dispatch_is
scrapy crawl au.nem.current.dispatch_scada

# nem archive data
scrapy crawl au.nem.archive.dispatch_is
scrapy crawl au.nem.archive.dispatch_scada
