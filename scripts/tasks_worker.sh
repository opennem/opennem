#!/usr/bin/env bash
set -exo pipefail

# if [ -z "$PYTHONPATH" ]
# then
#   export PYTHONPATH="$PWD:${PYTHONPATH}"
# else
#   export PYTHONPATH="/app"
# fi

if [ -z "$VIRTUAL_ENV" ]
then
  echo "Running in $VIRTUAL_ENV"
else
  source .venv/bin/activate
fi

huey_consumer -w4 -f -k process opennem.scheduler.huey
