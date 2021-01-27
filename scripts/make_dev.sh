set -euxo pipefail

git push -u origin master

scrapyd-deploy dev

rm -rf build/
