set -euxo pipefail

alembic upgrade head

python -m opennem.importer.rooftop
