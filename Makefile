.DEFAULT_GOAL := all
.SHELLFLAGS = -e
UPGRADE_ARGS ?= --upgrade
projectname = opennem

# tools
ruff-check = uv run ruff check $(projectname)
mypy = uv run mypy $(projectname)
pytest = uv run pytest tests -v
pyright = uv run pyright -v .venv $(projectname)
BUMP ?= dev

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
	@if ! echo "release major minor patch fix alpha beta rc rev post dev" | grep -w "$(BUMP)" > /dev/null; then \
		echo "Error: BUMP must be one of: release, major, minor, patch, fix, alpha, beta, rc, rev, post, dev"; \
		exit 1; \
	fi
	# if the branch is master then bump needs to be either major minor patch or release
	if [ "$$current_branch" = "master" ]; then \
		if [ "$$BUMP" != "major" ] && [ "$$BUMP" != "minor" ] && [ "$$BUMP" != "patch" ] && [ "$$BUMP" != "release" ] && [ "$$BUMP" != "rc" ]; then \
			echo "Error: Cannot bump on master branch unless it is major, minor, patch or release"; \
			exit 1; \
		fi \
	fi; \

	# if the current branch is dev then the bump type must be dev
	if [ "$$current_branch" = "dev" ]; then \
		if [ "$$BUMP" != "dev" ]; then \
			echo "Error: Cannot bump on dev branch unless it is dev"; \
			exit 1; \
		fi \
	fi; \

	uv version --bump $(BUMP)
	@NEW_VERSION=$$(uv version --short); \
	echo "New version: $$NEW_VERSION"; \
	git add pyproject.toml; \
	git commit -m "Bump version to $$NEW_VERSION"

.PHONY: tag
tag:
	$(eval CURRENT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD))
	$(eval NEW_VERSION := $(shell uv version --short))
	@if [ "$(CURRENT_BRANCH)" = "master" ]; then \
		git tag "$(NEW_VERSION)"; \
		echo "Pushing $(NEW_VERSION)"; \
		git push origin "$(NEW_VERSION)" "$(CURRENT_BRANCH)"; \
	else \
		git push -u origin "$(CURRENT_BRANCH)"; \
	fi


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
