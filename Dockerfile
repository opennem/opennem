FROM python:3.14-slim as python-base

ENV PROJECT_NAME="opennem" \
  PYTHONUNBUFFERED=1 \
  PYTHONFAULTHANDLER=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  PYSETUP_PATH="/opt/pysetup" \
  VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$VENV_PATH/bin:$PATH"

################################
# BUILDER
################################
FROM python-base as builder

RUN apt-get update \
  && apt-get install --no-install-recommends -y \
    build-essential \
    gcc \
    g++ \
    make \
    curl \
    git \
    ca-certificates \
    pkg-config \
    libssl-dev \
  && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR $PYSETUP_PATH

# Copy lock files first for better caching
COPY uv.lock pyproject.toml ./

# Minimal files needed for uv sync
RUN mkdir -p ${PROJECT_NAME} bin
COPY opennem/__init__.py ${PROJECT_NAME}/__init__.py
COPY LICENSE ./
COPY bin/run_server.py bin/

# Install dependencies with cache mount for faster rebuilds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

################################
# PRODUCTION
################################
FROM python-base as production

ENV FASTAPI_ENV=production

# Copy uv binary for runtime (needed for "uv run" commands)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install runtime dependencies and build tools (needed for Python 3.14 packages)
RUN apt-get update \
  && apt-get install --no-install-recommends -y \
    ca-certificates \
    build-essential \
    gcc \
    g++ \
    python3-dev \
  && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy venv from builder
COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH

# Copy application code
WORKDIR /app
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

EXPOSE 8000
