
# This builds the scrapyd container at opennem/scrapyd

poetry export --without-hashes -f requirements.txt > requirements.txt

docker build -t opennem/scrapyd -f Dockerfile.scrapyd .

docker push opennem/scrapyd

rm requirements.txt
