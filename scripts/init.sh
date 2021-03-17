#!/usr/bin/env bash
set -exo pipefail

pwd > .venv/lib/python3.8/site-packages/local.pth

if [ -z "$VIRTUAL_ENV" ]
then
  echo "Running in $VIRTUAL_ENV"
else
  source .venv/bin/activate
fi

alembic upgrade head

# Creates the db views
python -m opennem.cli db

# Initialzies fixtures and all the station, fac, emissions, etc. data
python -m opennem.cli db init


# Crawl initial data to bootstrap
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
scrapy crawl -L ERROR au.wem.live.pulse
scrapy crawl -L ERROR au.wem.current.facility_scada
scrapy crawl -L ERROR au.wem.current.balancing_summary

scrapy crawl -L ERROR au.nem.current.dispatch_scada
scrapy crawl -L ERROR au.nem.current.dispatch
scrapy crawl -L ERROR au.nem.current.dispatch_actual_gen
