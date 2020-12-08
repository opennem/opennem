#!/usr/bin/env bash
set -exo pipefail

if [ -z "$VIRTUAL_ENV" ]
then
  echo "Running in $VIRTUAL_ENV"
else
  source .venv/bin/activate
fi

scrapy crawl -L ERROR au.apvi.archive.data
scrapy crawl -L ERROR au.mms.archive
scrapy crawl -L ERROR au.nem.archive.dispatch
scrapy crawl -L ERROR au.nem.archive.dispatch_actual_gen
scrapy crawl -L ERROR au.nem.archive.dispatch_is
scrapy crawl -L ERROR au.nem.archive.dispatch_scada
scrapy crawl -L ERROR au.nem.archive.price
scrapy crawl -L ERROR au.nem.archive.rooftop
scrapy crawl -L ERROR au.wem.historic.balancing_summary
scrapy crawl -L ERROR au.wem.historic.facility_scada
scrapy crawl -L ERROR au.wem.historic.load_summary

python -m opennem.notifications.slack "**Notice** Finished running historic crawls on $ENV"
