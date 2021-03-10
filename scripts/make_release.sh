set -euxo pipefail

pytest

poetry version ${1-prerelease}

VERSION=$(poetry version | sed 's/opennem-backend\ //g')

echo "Building version $VERSION"

poetry export --format requirements.txt -E postgres > requirements.txt

git add pyproject.toml requirements.txt

git ci -m "v$VERSION"

git tag v$VERSION
git push -u origin master v$VERSION

docker build -f infra/container/Dockerfile -t opennem/opennem_backend:$VERSION .
docker push opennem/opennem_backend:$VERSION

# @TODO check that we're ready for relesae to make it :latest
docker tag  opennem/opennem_backend:$VERSION opennem/opennem_backend
# docker push opennem/opennem

poetry build

twine upload --skip-existing dist/*

scrapyd-deploy dev
# scrapyd-deploy prod

rm -rf build/
