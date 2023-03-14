.DEFAULT_GOAL := all
UPGRADE_ARGS ?= --upgrade
isort = isort opennem tests
black = black opennem tests
ruff = ruff opennem tests
pyright = pyright -v $(poetry env info -p) opennem

.PHONY: test
test:
	pytest tests -v

.PHONY: format
format:
	$(isort)
	$(black)
	$(ruff) --fix --exit-zero

.PHONY: pyright
pyright:
	$(pyright)

install:
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


.PHONY: install build release pyright
