FROM python:3.11 as python-base

# python
ENV PROJECT_NAME="opennem" \
  PYTHONUNBUFFERED=1 \
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  # prevents python creating .pyc files
  PYTHONDONTWRITEBYTECODE=1 \
  \
  # pip
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  \
  # poetry
  # https://python-poetry.org/docs/configuration/#using-environment-variables
  POETRY_VERSION=1.6.1 \
  # make poetry install to this location
  POETRY_HOME="/opt/poetry" \
  # make poetry create the virtual environment in the project's root
  # it gets named `.venv`
  POETRY_VIRTUALENVS_IN_PROJECT=true \
  # do not ask any interactive question
  POETRY_NO_INTERACTION=1 \
  \
  # paths
  # this is where our requirements + virtual environment will live
  PYSETUP_PATH="/opt/pysetup" \
  VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

################################
# BUILDER-BASE
# Used to build deps + create our virtual environment
################################
FROM python-base as builder-base
RUN apt-get update \
  && apt-get install --no-install-recommends -y \
  # deps for installing poetry
  curl \
  # deps for building python deps
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
# The --mount will mount the buildx cache directory to where
# Poetry and Pip store their cache so that they can re-use it
RUN --mount=type=cache,id=cache-poetry-install,target=/root/.cache \
  curl -sSL https://install.python-poetry.org | python3 -

RUN poetry config installer.max-workers 10

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

# workaround for if you have packages-include in your pyproject.toml
RUN mkdir ${PROJECT_NAME} && touch ${PROJECT_NAME}/__init__.py

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN --mount=type=cache,id=cache-poetry,target=/root/.cache \
  poetry install --without=dev --no-interaction --no-ansi -v


# `development` image is used during development / testing
FROM python-base as development
ENV FASTAPI_ENV=development
WORKDIR $PYSETUP_PATH

# copy in our built poetry + venv
COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

# quicker install as runtime deps are already installed
RUN poetry install --no-interaction --no-ansi -v

# will become mountpoint of our code
WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "--reload", "opennem.api.app:app"]


# `production` image used for runtime
FROM python-base as production
ENV FASTAPI_ENV=production
ENV PYTHONPATH="$PYTHONPATH:/app"
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH
COPY . /app/

# silly hack to get huey and other bin running running and finding modules
RUN cp /opt/pysetup/.venv/bin/huey_consumer /app

EXPOSE 8000
WORKDIR /app
