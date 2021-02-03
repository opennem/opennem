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

python -m opennem.cli db init

python -m opennem.cli db views

python -m opennem.importer.wikidata

# import emission maps
python -m opennem.cli import emissions

# run rooftop
./scripts/spider_queue.py rooftop

# run dispatch_id
./scripts/spider_queue.py dispatch_is
