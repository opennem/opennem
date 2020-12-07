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

python -m opennem.importer.rooftop

python -m opennem.importer.emissions

python -m opennem.importer.interconnectors

# since we changed the APVI network we need to
# run the archive again
scrapy crawl au.apvi.archive.data
