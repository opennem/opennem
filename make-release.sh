set -euxo pipefail

poetry version ${1-prerelease}

VERSION=$(poetry version | sed 's/opennem\ //g')

echo "Building version $VERSION"

poetry export --format requirements.txt -E postgres > requirements.txt

git add pyproject.toml requirements.txt

git ci -m "v$VERSION"

git tag v$VERSION
git push -u origin master v$VERSION

docker build -t opennem/opennem:$VERSION .
docker push opennem/opennem:$VERSION

# @TODO check that we're ready for relesae to make it :latest
# docker tag  opennem/opennem:$VERSION opennem/opennem
# docker push opennem/opennem

poetry build

twine upload dist/*

scrapyd-deploy

rm -rf build/
