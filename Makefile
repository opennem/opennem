.DEFAULT_GOAL := all
.SHELLFLAGS = -e
UPGRADE_ARGS ?= --upgrade
projectname = opennem

# tools
black = poetry run black $(projectname) tests
ruff = poetry run ruff $(projectname) tests
mypy = poetry run mypy $(projectname) tests
pytest = poetry run pytest tests -v
pyright = poetry run pyright -v $(poetry env info -p) $(projectname)
version_file = $(projectname)/__init__.py
bump=prerelease

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
	git add $(version_file) pyproject.toml; \
	git commit -m "Bump version: $$new_version"; \
	git tag $$new_version; \
	git push origin $$current_branch; \
	git push origin $$new_version

.PHONY: image
image:
	docker build \
		--tag opennem/base:latest \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		--cache-from pagecog/base:latest \
		.

.PHONY: clean
clean:
	ruff clean
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete -o -type d -name .mypy_cache -delete
	rm -rf build

.PHONY: codecov
codecov:
	pytest --cov=./$(projectname)

release: format lint version
