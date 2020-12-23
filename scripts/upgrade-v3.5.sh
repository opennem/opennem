#!/usr/bin/env bash
set -exo pipefail

if [ -z "$PYTHONPATH" ]
then
  export PYTHONPATH="$PWD:${PYTHONPATH}"
else
  export PYTHONPATH="/app"
fi

if [ -z "$VIRTUAL_ENV" ]
then
  echo "Running in $VIRTUAL_ENV"
else
  source .venv/bin/activate
fi

alembic upgrade head

python -m opennem.db.load_fixtures

scrapy crawl -L ERROR au.mms.archive.rooftop_actual
scrapy crawl -L ERROR au.nem.archive.rooftop
scrapy crawl -L ERROR au.nem.current.rooftop

python -m opennem.importer.emissions

python -m opennem.api.export.tasks
