set -euxo pipefail

alembic upgrade head

python -m opennem.db.load_fixtures

python -m opennem.importer.rooftop

python -m opennem.importer.pollution
