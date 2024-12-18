.DEFAULT_GOAL := all
.SHELLFLAGS = -e
UPGRADE_ARGS ?= --upgrade
projectname = opennem

# tools
ruff-check = uv run ruff check $(projectname)
mypy = uv run mypy $(projectname)
pytest = uv run pytest tests -v
pyright = uv run pyright -v .venv $(projectname)
hatch = uvx hatch
BUMP_TYPE ?= dev

.PHONY: test
test:
	$(pytest)

.PHONY: format
format:
	uv run ruff format $(projectname)
	$(ruff-check) --fix

.PHONY: lint
lint:
	$(ruff-check) --exit-zero

.PHONY: check
check:
	$(pyright)


.PHONY: build
build:
	pip install wheel
	python setup.py sdist bdist_wheel


.PHONY: version
version:
	@if ! echo "release major minor patch fix alpha beta rc rev post dev" | grep -w "$(BUMP_TYPE)" > /dev/null; then \
		echo "Error: BUMP_TYPE must be one of: release, major, minor, patch, fix, alpha, beta, rc, rev, post, dev"; \
		exit 1; \
	fi
	# if the branch is master then bump needs to be either major minor patch or release
	if [ "$$current_branch" = "master" ]; then \
		if [ "$$BUMP_TYPE" != "major" ] && [ "$$BUMP_TYPE" != "minor" ] && [ "$$BUMP_TYPE" != "patch" ] && [ "$$BUMP_TYPE" != "release" ]; then \
			echo "Error: Cannot bump on master branch unless it is major, minor, patch or release"; \
			exit 1; \
		fi \
	fi; \
	$(hatch) version $(BUMP_TYPE)
	git add opennem/__init__.py
	git commit -m "Bump version to $(NEW_VERSION)"

.PHONY: tag
tag:
	$(eval CURRENT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD))
	$(eval NEW_VERSION := $(shell uvx hatch version))
	@if [ "$(CURRENT_BRANCH)" = "master" ]; then \
		if [[ "$(NEW_VERSION)" != *"release"* ]]; then \
			echo "Error: Cannot tag non-release on master branch"; \
			exit 1; \
		fi \
	fi
	git tag $(NEW_VERSION)
	@echo "Pushing $(NEW_VERSION)"
	git push -u origin $(NEW_VERSION) $(CURRENT_BRANCH)

.PHONY: release-pre
release-pre: format lint

.PHONY: release
release: release-pre version tag

.PHONY: image
image:
	docker buildx build \
		--tag opennem/base:latest \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		.

.PHONY: test-worker
test-worker:
	docker run --rm -it --env-file .env.test opennem/base:latest huey_consumer -w4 -f -k process opennem.workers.scheduler.huey

.PHONY: test-api
test-api:
	docker run --rm -it -P --env-file .env.test opennem/base:latest uvicorn --host 0.0.0.0 --port 8000 opennem.api.app:app

.PHONY: image-shell
image-shell:
	docker run --rm -it --env-file .env.test opennem/base:latest bash


.PHONY: clean
clean:
	ruff clean
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete -o -type d -name .mypy_cache -delete
	rm -rf build

.PHONY: codecov
codecov:
	pytest --cov=./$(projectname)
