#!/usr/bin/env bash
set -exo pipefail

if [ -z "$VIRTUAL_ENV" ]
then
  echo "Running in $VIRTUAL_ENV"
else
  source .venv/bin/activate
fi

# apvi
scrapy crawl -L ERROR au.apvi.current.data

# stats data wem
scrapy crawl -L ERROR au.wem.live.facility_intervals
scrapy crawl -L ERROR au.wem.live.pulse
scrapy crawl -L ERROR au.wem.current.facility_scada
scrapy crawl -L ERROR au.wem.current.balancing_summary

# nem
scrapy crawl -L ERROR au.nem.day.dispatch_scada
scrapy crawl -L ERROR au.nem.day.dispatch_is
scrapy crawl -L ERROR au.nem.day.trading_is
scrapy crawl -L ERROR au.nem.current.rooftop
scrapy crawl -L ERROR au.nem.current.rooftop_forecast
scrapy crawl -L ERROR au.nem.current.dispatch_actual_gen
scrapy crawl -L ERROR au.nem.current.dispatch
scrapy crawl -L ERROR au.nem.current.trading_is
# scrapy crawl -L ERROR au.nem.current.price

# bom
scrapy crawl bom.all
scrapy crawl bom.capitals
