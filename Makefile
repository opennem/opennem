.DEFAULT_GOAL := all
.SHELLFLAGS = -e
UPGRADE_ARGS ?= --upgrade
projectname = opennem

# tools
ruff-check = poetry run ruff check $(projectname)
mypy = poetry run mypy $(projectname)
pytest = poetry run pytest tests -v
pyright = poetry run pyright -v $(poetry env info -p) $(projectname)
version_file = $(projectname)/__init__.py
bump=prerelease

.PHONY: test
test:
	$(pytest)

.PHONY: format
format:
	poetry run ruff format $(projectname)
	$(ruff-check) --fix

.PHONY: lint
lint:
	$(ruff-check) --exit-zero

.PHONY: check
check:
	$(pyright)

.PHONE: requirements
requirements:
	poetry export -o requirements.txt

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

.PHONY: release-pre
release-pre: format lint requirements

.PHONY: image
image:
	docker buildx build \
		--tag opennem/base:latest \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		.

.PHONY: clean
clean:
	ruff clean
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete -o -type d -name .mypy_cache -delete
	rm -rf build

.PHONY: codecov
codecov:
	pytest --cov=./$(projectname)

release: release-pre version
