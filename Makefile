.DEFAULT_GOAL := all
.SHELLFLAGS = -e
UPGRADE_ARGS ?= --upgrade
projectname = opennem

# tools
ruff-check = uv run ruff check $(projectname)
mypy = uv run mypy $(projectname)
pytest = uv run pytest tests -v
pyright = uv run pyright -v .venv $(projectname)
BUMP_TYPE ?= pre_n

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


.PHONE: version
version:
	@if ! echo "major minor patch pre_l pre_n" | grep -w "$(BUMP_TYPE)" > /dev/null; then \
		echo "Error: BUMP_TYPE must be one of: major, minor, patch, pre_l, pre_n"; \
		exit 1; \
	fi
	@uv run bump-my-version bump $(BUMP_TYPE)
	@new_version=$$(uv run --python 3.12 python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['tool']['bumpversion']['current_version'])"); \
	echo "Pushing $$new_version"; \
	git push -u origin $$new_version

.PHONY: release-pre
release-pre: format lint

.PHONY: release
release: release-pre version

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
