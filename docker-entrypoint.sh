#!/bin/sh

set -e

. .venv/bin/activate

exec /code/.venv/bin/alembic upgrade head

exec "$@"
