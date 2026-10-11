# Python 3.12 matches requires-python (<3.13) in pyproject/uv.lock. The previous
# python:3.14-slim base did not satisfy it, so uv downloaded a managed 3.12 into /root
# and the copied venv pointed at an interpreter appuser cannot read.
FROM python:3.12-slim AS python-base

ENV PROJECT_NAME="opennem" \
  PYTHONUNBUFFERED=1 \
  PYTHONFAULTHANDLER=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  UV_PYTHON_DOWNLOADS=never \
  UV_PYTHON=/usr/local/bin/python3.12 \
  UV_LINK_MODE=copy \
  UV_PROJECT_ENVIRONMENT=/app/.venv

ENV PATH="/app/.venv/bin:$PATH"

################################
# BUILDER (compilers live only here)
################################
FROM python-base AS builder

RUN apt-get update \
  && apt-get install --no-install-recommends -y \
    build-essential \
    pkg-config \
    libssl-dev \
  && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /uvx /bin/

WORKDIR /app

# Dependencies only: cached until uv.lock / pyproject.toml change
COPY uv.lock pyproject.toml LICENSE ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Project itself (editable, points at /app)
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

################################
# PRODUCTION
################################
FROM python-base AS production

ENV FASTAPI_ENV=production \
  UV_NO_SYNC=1 \
  UV_OFFLINE=1 \
  MALLOC_ARENA_MAX=2

COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /uvx /bin/

# Runtime only: chromium for html2image social cards, no compilers
RUN apt-get update \
  && apt-get install --no-install-recommends -y \
    ca-certificates \
    chromium \
  && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMIUM_FLAGS="--no-sandbox --headless --disable-gpu"

# -m is required: chromium >= 150 derives its crashpad database path from $HOME,
# and aborts on startup ("--database is required", exit 133) when it doesn't exist.
RUN groupadd -r appuser && useradd -r -m -g appuser appuser

WORKDIR /app
COPY --from=builder --chown=appuser:appuser /app /app

USER appuser

EXPOSE 8000
