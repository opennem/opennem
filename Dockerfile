FROM python:3.8 as base

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100

FROM base as app

WORKDIR /code

COPY requirements.txt /code/

# Project initialization:
RUN python -m venv .venv
RUN . .venv/bin/activate
RUN pip install -r requirements.txt

# Creating folders, and files for a project:
FROM app

COPY opennem /code/opennem/
COPY docker-entrypoint.sh /entrypoint.sh

EXPOSE 8000
WORKDIR /code
ENV PATH="/code/.venv/bin:${PATH}"

ENTRYPOINT [ "/entrypoint.sh" ]
