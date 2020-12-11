set -euxo pipefail

git push -u origin master

scrapyd-deploy dev
scrapyd-deploy prod

rm -rf build/
