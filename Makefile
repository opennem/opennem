.DEFAULT_GOAL := all
UPGRADE_ARGS ?= --upgrade
projectname = opennem

# tools
black = poetry run black $(projectname) tests
ruff = poetry run ruff $(projectname) tests
mypy = poetry run mypy $(projectname) tests
pytest = poetry run pytest tests -v
pyright = poetry run pyright -v $(poetry env info -p) $(projectname)
bumpver = poetry run bumpver update -n

.PHONY: test
test:
	$(pytest)

.PHONY: format
format:
	$(black)
	$(ruff) --fix

.PHONY: lint
lint:
	$(ruff) --exit-zero

.PHONY: check
check:
	$(pyright)

.PHONY: install
install:
	pip install -r ./requirements.txt

.PHONY: build
build:
	pip install wheel
	python setup.py sdist bdist_wheel

.PHONY: bump-dev
bump-dev:
	$(bumpver) --tag-num

.PHONY: bump-patch
bump-patch:
	$(bumpver) --patch

.PHONY: image
image:
	docker build \
		--tag opennem/base:latest \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		--cache-from pagecog/base:latest \
		.

.PHONY: release-pre
release-pre: format lint

.PHONY: clean
clean:
	ruff clean
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete -o -type d -name .mypy_cache -delete
	rm -rf build

.PHONY: codecov
codecov:
	pytest --cov=./$(projectname)

release: release-pre bump-dev

release-patch: release-pre bump-patch

release-major: release-pre bump-major
