FROM python:3.12-bullseye as python-base

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

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

################################
# BUILDER-BASE
# Used to build deps + create our virtual environment
################################
FROM python-base as builder-base
RUN apt-get update \
  && apt-get install --no-install-recommends -y \
  # deps for building python deps
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# install uv
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod -R 655 /install.sh && /install.sh && rm /install.sh

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY requirements.txt pyproject.toml ./

# workaround for if you have packages-include in your pyproject.toml
RUN mkdir ${PROJECT_NAME} && touch ${PROJECT_NAME}/__init__.py

# install runtime deps - using UV
RUN /root/.cargo/bin/uv venv ${VENV_PATH}
RUN /root/.cargo/bin/uv pip install --no-cache -r requirements.txt

# `development` image is used during development / testing
FROM python-base as development
ENV FASTAPI_ENV=development
WORKDIR $PYSETUP_PATH

# copy in our built poetry + venv
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

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
