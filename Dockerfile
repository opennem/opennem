FROM python:3.13-bullseye as python-base

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
  # paths
  # this is where our requirements + virtual environment will live
  PYSETUP_PATH="/opt/pysetup" \
  VENV_PATH="/opt/pysetup/.venv"

# prepend venv to path
ENV PATH="$VENV_PATH/bin:$PATH"

################################
# BUILDER-BASE
# Used to build deps + create our virtual environment
################################
FROM python-base as builder-base
RUN apt-get update \
  && apt-get install --no-install-recommends -y \
  build-essential \
  curl \
  ca-certificates \
  pkg-config \
  libssl-dev \
  && rm -rf /var/lib/apt/lists/*

# Install Rust toolchain
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY uv.lock pyproject.toml ./

# workaround for if you have packages-include in your pyproject.toml
RUN mkdir ${PROJECT_NAME} && touch ${PROJECT_NAME}/__init__.py

# install runtime deps - using UV
RUN uv sync

# `development` image is used during development / testing
FROM python-base as development
ENV FASTAPI_ENV=development
WORKDIR $PYSETUP_PATH

# copy in our built venv
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

# will become mountpoint of our code
WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "--reload", "opennem.api.app:app"]

# `production` image used for runtime
FROM python-base as production
ENV FASTAPI_ENV=production
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH
COPY . /app/

EXPOSE 8000
WORKDIR /app
