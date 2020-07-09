poetry version $@

VERSION=$(poetry version | sed 's/[^0-9\.]*//g')

docker build -t opennem/opennem .
docker push opennem/opennem

docker tag opennem/opennem opennem/opennem:$VERSION

poetry build

twine upload dist/*

git add pyproject.toml

git ci -m "v$VERSION"

git tag v$VERSION
git push -u origin master v$VERSION
