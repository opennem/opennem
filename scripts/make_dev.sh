set -euxo pipefail

VERSION=$(poetry version | sed 's/opennem\ //g')

echo "Building version $VERSION"

poetry export --format requirements.txt -E postgres > requirements.txt

git add pyproject.toml requirements.txt

git ci -m "v$VERSION"

git push -u origin master

scrapyd-deploy dev

rm -rf build/
