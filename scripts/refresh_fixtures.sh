#!/usr/bin/env zsh
# Script that grabs latest power and energy data
# and refreshes local fixtures
set -euo pipefail

echo "Refreshing fixtures"

CURRENT_YEAR=$(date +%Y)
REGIONS_ALL=("NSW1" "QLD1" "VIC1" "TAS1" "SA1")
REGION_TO_FETCH="NSW1"
WEEK_TO_FETCH="36"

# refresh exports
python -c "from opennem.schema.network import NetworkNEM; from opennem.exporter.historic import export_historic_for_year_and_week_no; export_historic_for_year_and_week_no(2022, 36, [NetworkNEM])"

for i in "${REGIONS_ALL[@]}"
do
   :
  print "Fetching https://data.dev.opennem.org.au/v3/stats/historic/weekly/NEM/${i:u}/year/2022/week/36.json"
  curl https://data.dev.opennem.org.au/v3/stats/historic/weekly/NEM/${i:u}/year/2022/week/${WEEK_TO_FETCH}.json --output - --silent | jq . > tests/fixtures/nem_${i:l}_week.json
  git add tests/fixtures/nem_${i:l}_week.json

done

print "Fetching https://data.dev.opennem.org.au/v3/stats/au/NEM/${REGION_TO_FETCH:u}/power/7d.json"
curl https://data.opennem.org.au/v3/stats/au/NEM/${REGION_TO_FETCH:u}/power/7d.json --output - --silent | jq . > tests/fixtures/nem_${REGION_TO_FETCH:l}_7d.json

print "Fetching https://data.dev.opennem.org.au/v3/stats/au/NEM/${REGION_TO_FETCH:u}/energy/${CURRENT_YEAR}.json"
curl https://data.opennem.org.au/v3/stats/au/NEM/${REGION_TO_FETCH:u}/energy/${CURRENT_YEAR}.json --output - --silent | jq . > tests/fixtures/nem_${REGION_TO_FETCH:l}_1y.json


git add tests/fixtures/nem_${REGION_TO_FETCH:l}_7d.json
git add tests/fixtures/nem_${REGION_TO_FETCH:l}_1y.json

git commit -m "Refreshed fixtures for ${REGION_TO_FETCH:l}"
