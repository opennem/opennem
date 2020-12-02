set -euxo pipefail

# fix for containers
export PYTHONPATH="$CWD:$PYTHONPATH"

alembic upgrade head

python -m opennem.db.load_fixtures

python -m opennem.importer.rooftop

python -m opennem.importer.emissions
