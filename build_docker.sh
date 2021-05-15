#!/usr/bin/env bash

set -euxo pipefail

docker build -t opennem/database:dev -f infra/database/Dockerfile .
docker-compose up -d --force-recreate --remove-orphans database
docker-compose logs -f database
