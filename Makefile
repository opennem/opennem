.DEFAULT_GOAL := all
.SHELLFLAGS = -e
UPGRADE_ARGS ?= --upgrade
projectname = opennem

# tools
ruff-check = uv run ruff check $(projectname)
mypy = uv run mypy $(projectname)
pytest = uv run pytest tests -v
pyright = uv run pyright -v .venv $(projectname)
version_file = $(projectname)/__init__.py
bump=prerelease

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
	@git diff --cached --exit-code || (echo "There are staged but uncommitted changes. Please commit or unstage them first." && exit 1)
	poetry version $(bump)
	@new_version=$$(poetry version -s); \
	current_branch=$$(git rev-parse --abbrev-ref HEAD); \
	echo "Updating $(version_file) to $$new_version"; \
	if [ "$$(uname)" = "Darwin" ]; then \
		sed -i '' "s/__version__ = \".*\"/__version__ = \"$$new_version\"/g" $(version_file); \
	else \
		sed -i "s/__version__ = \".*\"/__version__ = \"$$new_version\"/g" $(version_file); \
	fi; \
	git add $(version_file) pyproject.toml requirements.txt; \
	git commit -m "Bump version: $$new_version"; \
	git tag $$new_version; \
	git push origin $$current_branch; \
	git push origin $$new_version

.PHONE: push
push:
	@uv run bump-my-version bump pre_n
	git push -u origin

.PHONY: release-pre
release-pre: format lint

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

release: release-pre version
