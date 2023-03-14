set -euxo pipefail

# @TODO migrate this file to Makefile

if [[ "${TRACE-0}" == "1" ]]; then set -o xtrace; fi

#pytest

make format

# run pyright
# pyright --stats opennem/

bumpver update --${1-patch}

VERSION=$(poetry version -s)
echo "Building version $VERSION"

poetry export --format requirements.txt -E postgres --without-hashes > requirements.txt
poetry export --with dev --format requirements.txt --without-hashes > requirements_dev.txt
git add requirements.txt requirements_dev.txt

git ci -m "v$VERSION"

git tag v$VERSION
git push -u origin master v$VERSION
