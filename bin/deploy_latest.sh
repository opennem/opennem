#!/usr/bin/env bash

set -euo pipefail

. ${PWD}/scripts/_functions.sh

_log "Starting deploy"

VERSION=$(poetry version | sed 's/opennem-backend\ //g')

cd infra/dev/

VERSION=$VERSION docker-compose up -d

cd ../../

_log "Done"
