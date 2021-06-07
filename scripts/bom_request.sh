#!/usr/bin/env bash

# Test BoM requests to figure out what requests work
set -euxo pipefail

curl \
  -o /dev/null \
  -s \
  -D - \
  -v \
  -X GET \
  -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9" \
  -H "Accept-Language: en-GB,en-US;q=0.9,en;q=0.8" \
  -H "Connection: keep-alive" \
  http://www.bom.gov.au/fwo/IDD60801/IDD60801.94120.json
