FROM python:3.12-bullseye as python-base

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
# BUILDER-BASE
################################
FROM python-base as builder-base

RUN apt-get update \
  && apt-get install --no-install-recommends -y \
    build-essential \
    curl \
    git \
    ca-certificates \
    pkg-config \
    libssl-dev \
  && rm -rf /var/lib/apt/lists/*

# Install Rust toolchain (needed for curl-cffi and other packages)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

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

# Install runtime deps
RUN uv sync --frozen

################################
# PRODUCTION
################################
FROM python-base as production

ENV FASTAPI_ENV=production

# Copy uv binary for runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy venv from builder
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

# Copy application code
WORKDIR /app
COPY . .

EXPOSE 8000
