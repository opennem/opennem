FROM python:3.8 as base

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100

FROM base as code_install

WORKDIR /code_install

COPY requirements.txt /code_install/

# Project initialization:
RUN python -m venv .venv
RUN chmod +x .venv/bin/activate
RUN .venv/bin/activate
RUN pip install -r requirements.txt

# Creating folders, and files for a project:
FROM code_install as app

WORKDIR /app

RUN mv /code_install/.venv /app/.venv
COPY . /app
COPY docker-entrypoint.sh /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT [ "/app/entrypoint.sh" ]
