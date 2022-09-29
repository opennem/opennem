#!/usr/bin/env zsh
# Script that grabs latest power and energy data
# and refreshes local fixtures
set -euo pipefail

echo "Refreshing fixtures"

CURRENT_YEAR=$(date +%Y)
REGIONS_ALL=("NSW1" "QLD1" "VIC1" "TAS1" "SA1")
WEEK_TO_FETCH=$(($(date +%U) - 1))

# refresh exports
./scripts/fixtures.py

for REGION_TO_FETCH in "${REGIONS_ALL[@]}"
do
   :
  print "Fetching https://data.dev.opennem.org.au/v3/stats/historic/weekly/NEM/${REGION_TO_FETCH:u}/year/2022/week/${WEEK_TO_FETCH}.json"
  curl https://data.dev.opennem.org.au/v3/stats/historic/weekly/NEM/${REGION_TO_FETCH:u}/year/2022/week/${WEEK_TO_FETCH}.json --output - --silent | jq . > tests/fixtures/nem_${REGION_TO_FETCH:l}_week.json
  git add tests/fixtures/nem_${REGION_TO_FETCH:l}_week.json

  print "Fetching https://data.dev.opennem.org.au/v3/stats/au/NEM/${REGION_TO_FETCH:u}/power/7d.json"
  curl https://data.dev.opennem.org.au/v3/stats/au/NEM/${REGION_TO_FETCH:u}/power/7d.json --output - --silent | jq . > tests/fixtures/nem_${REGION_TO_FETCH:l}_7d.json
  git add tests/fixtures/nem_${REGION_TO_FETCH:l}_7d.json

  print "Fetching https://data.dev.opennem.org.au/v3/stats/au/NEM/${REGION_TO_FETCH:u}/energy/${CURRENT_YEAR}.json"
  curl https://data.dev.opennem.org.au/v3/stats/au/NEM/${REGION_TO_FETCH:u}/energy/${CURRENT_YEAR}.json --output - --silent | jq . > tests/fixtures/nem_${REGION_TO_FETCH:l}_1y.json
  git add tests/fixtures/nem_${REGION_TO_FETCH:l}_1y.json

  print "Fetching https://data.dev.opennem.org.au/v3/stats/au/NEM/${REGION_TO_FETCH:u}/energy/all.json"
  curl https://data.dev.opennem.org.au/v3/stats/au/NEM/${REGION_TO_FETCH:u}/energy/all.json --output - --silent | jq . > tests/fixtures/nem_${REGION_TO_FETCH:l}_all.json
  git add tests/fixtures/nem_${REGION_TO_FETCH:l}_all.json

done

git commit -m "Refreshed fixtures all regions"
