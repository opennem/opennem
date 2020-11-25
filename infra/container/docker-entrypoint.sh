#!/bin/bash

set -e

source /app/.venv/bin/activate

exec "$@"
