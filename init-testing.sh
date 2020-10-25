set -euxo pipefail

ENV=testing alembic upgrade head

ENV=testing python -m opennem.cli db init
