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

# python -m opennem.cli db views

python -m opennem.importer.wikidata
python -m opennem.importer.interconnectors
python -m opennem.cli import emissions
python -m opennem.importer.trading_flows
