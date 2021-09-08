UPGRADE_ARGS ?= --upgrade

test:
	pytest tests -v

tox-test:
	tox -p all

pylint:
	tox -e pylint

black:
	black -l 120 opennem docs tests setup.py
	black -v --ipynb notebooks/*.ipynb

mypy:
	mypy --config-file ./mypy.ini opennem

install:
	# ARCHFLAGS="-arch x86_64" pip install -r ./requirements.txt
	pip install -r ./requirements.txt

build:
	pip install wheel
	python setup.py sdist bdist_wheel

pyclean:
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

cleandist:
	rm -rf build

codecov:
	pytest --cov=./opennem

release: build
	pip install twine
	twine check dist/*
	twine upload dist/*

spider_deploy:
	scrapyd-deploy dev

.PHONY: test black install build release
