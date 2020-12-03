set -euxo pipefail

# fix for containers
export PYTHONPATH="$PWD:$PYTHONPATH"

# activate venv
source .venv/bin/activate

alembic upgrade head

python -m opennem.db.load_fixtures

python -m opennem.importer.rooftop

python -m opennem.importer.emissions

python -m opennem.importer.interconnectors
