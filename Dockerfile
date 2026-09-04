FROM cgr.dev/chainguard/wolfi-base:latest@sha256:003627df3c1e1bba0c4116afcddb314aca9594ee2328c7e876a8081a6c988b2e AS base

ARG PYTHON_VERSION=3.14

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install runtime dependencies. Versions deliberately unpinned: Wolfi rolls
# forward and garbage-collects old versions, so an "=<version>" pin breaks the
# build within days. The guardrails are the version-scoped names plus the
# digest above. No pip: uv (below) installs everything.
#   libstdc++  NOT optional: the rasterio/pyproj/duckdb manylinux wheels list
#              libstdc++.so.6 in DT_NEEDED and auditwheel does not vendor it.
#   bash, tzdata, curl  parity with the old Debian base: /bin/sh is busybox,
#              Wolfi ships no /usr/share/zoneinfo, curl is for in-pod debugging.
RUN apk add --no-cache \
      python-${PYTHON_VERSION} \
      libstdc++ bash tzdata curl libexpat1

# uv as a pass-through stage rather than a direct COPY --from=<image>:
# Dependabot only parses FROM lines (dependabot/dependabot-core#5103), so this
# keeps the version pinned *and* auto-updated by the docker ecosystem.
FROM ghcr.io/astral-sh/uv:0.12.9@sha256:8b940d3a9d65bed080436972241af2e21c84b5e8c9193f7014ed71479ee795ff AS uv

# Build stage
FROM base AS builder

ARG PYTHON_VERSION

# Set build labels
LABEL stage=builder
LABEL org.opencontainers.image.source="https://github.com/developmentseed/titiler-stacapi"
LABEL org.opencontainers.image.description="TiTiler STAC API"
LABEL org.opencontainers.image.licenses="MIT"

# Install uv
COPY --from=uv /uv /uvx /usr/local/bin/

# Configure uv-managed virtual environment
#   UV_PYTHON: the apk python above, so the venv's interpreter symlinks resolve
#     against the same path in the runtime stage
#   UV_COMPILE_BYTECODE: .pyc at install time, as pip did, so cold starts
#     don't pay the compile on first import
ENV UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=python${PYTHON_VERSION} \
    UV_COMPILE_BYTECODE=1 \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /tmp/app

# Copy project metadata and dependencies
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --frozen --no-dev --extra server --no-install-project

# Copy and install runtime source code to the builder image
COPY titiler/ titiler/
RUN uv pip install --no-deps .

# Runtime stage
FROM base

# Set runtime labels
LABEL org.opencontainers.image.source="https://github.com/developmentseed/titiler-stacapi"
LABEL org.opencontainers.image.description="TiTiler STAC API"
LABEL org.opencontainers.image.licenses="MIT"

# The chart execs `command: ["uvicorn"]` — a bare binary, resolved against the
# image's PATH.
ENV PATH="/opt/venv/bin:${PATH}"

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

WORKDIR /tmp

USER nonroot

###################################################
# For compatibility (might be removed at one point)
ENV MODULE_NAME=titiler.stacapi.main
ENV VARIABLE_NAME=app
ENV HOST=0.0.0.0
ENV PORT=80
ENV WEB_CONCURRENCY=1
CMD gunicorn -k uvicorn.workers.UvicornWorker ${MODULE_NAME}:${VARIABLE_NAME} --bind ${HOST}:${PORT} --workers ${WEB_CONCURRENCY}
