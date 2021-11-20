#!/usr/bin/env bash
set -euo pipefail

# set local path
pwd > .venv/lib/python3.9/site-packages/local.pth

if [ -z "$VIRTUAL_ENV" ]
then
  echo "Running in $VIRTUAL_ENV"
else
  source .venv/bin/activate
fi

alembic upgrade head

# Initialzies fixtures and all the station, fac, emissions, etc. data
python -m opennem.cli db init

python -m opennem.cli db views

# CRAWLS

# bom data
scrapy crawl -L ERROR bom.capitals

# rooftop
scrapy crawl -L ERROR au.apvi.current.data

# wem
scrapy crawl -L ERROR au.wem.participant
scrapy crawl -L ERROR au.wem.facilities
scrapy crawl -L ERROR au.wem.live.facility_intervals
scrapy crawl -L ERROR au.wem.live.pulse
scrapy crawl -L ERROR au.wem.current.facility_scada
scrapy crawl -L ERROR au.wem.current.balancing_summary

# nem
scrapy crawl -L ERROR au.nem.day.dispatch_is
scrapy crawl -L ERROR au.nem.day.dispatch_scada
# scrapy crawl -L ERROR au.nem.current.rooftop
# scrapy crawl -L ERROR au.nem.current.trading_is
# scrapy crawl -L ERROR au.nem.current.dispatch
# scrapy crawl -L ERROR au.nem.current.dispatch_actual_gen


# update seen ranges
python -m opennem.workers.facility_data_ranges

# refresh views
# python -m opennem.cli db refresh
