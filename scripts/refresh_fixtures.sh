#!/usr/bin/env zsh
# Script that grabs latest power and energy data
# and refreshes local fixtures
set -euo pipefail

echo "Refreshing fixtures"

CURRENT_YEAR=$(date +%Y)
REGION_TO_FETCH="NSW1"

curl https://data.dev.opennem.org.au/v3/stats/au/NEM/${REGION_TO_FETCH:u}/power/7d.json --output - --silent | jq . > tests/fixtures/nem_${REGION_TO_FETCH:l}_7d.json

curl https://data.dev.opennem.org.au/v3/stats/au/NEM/${REGION_TO_FETCH:u}/energy/${CURRENT_YEAR}.json --output - --silent | jq . > tests/fixtures/nem_${REGION_TO_FETCH:l}_1y.json

# git add tests/fixtures/nem_${name,l}_7d.json
# git add tests/fixtures/nem_${name,l}_1y.json

# git s .
