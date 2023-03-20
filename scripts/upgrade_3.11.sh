#!/usr/bin/env bash

# db migration
alembic upgrade head

# fix gap in flows
./scripts/import_old_aggregate_flows.py

# rooftop backfill
./scripts/rooftop_backfill.py

# run all aggregates
python -m opennem.aggregates.facility_daily
