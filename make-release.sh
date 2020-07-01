poetry version patch

VERSION=$(poetry version | sed 's/[^0-9\.]*//g')

docker build -t opennem/opennem .
docker push opennem/opennem

docker tag opennem/opennem opennem/opennem:$VERSION

twine upload dist/*

git tag v$VERSION
git push -u origin master v$VERSION
