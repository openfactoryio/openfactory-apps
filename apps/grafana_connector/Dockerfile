# ------------------------------------------------------------------------------
# 🐳 Dockerfile for OpenFactory Grafana Connector
#
# build:
#   docker build -t openfactory-grafana-connector .
# ------------------------------------------------------------------------------

# ---- builder stage ----
FROM python:3.12-slim AS builder

# Argument for version management
ARG OFA_VERSION=main

# Install git
RUN apt-get update && apt-get install -y git

# Create virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
       "openfactory[fastapi] @ git+https://github.com/openfactoryio/openfactory-core.git@${OFA_VERSION}" \
    && pip install --no-cache-dir asyncua

# ---- final stage ----
FROM python:3.12-slim

# Arguments for non-root user creation
ARG UNAME=grafana-connector
ARG UID=1200
ARG GID=1200

# Argument for version management
ARG VERSION=dev

# Create runtime user/group
RUN groupadd --gid $GID $UNAME \
    && useradd --create-home --uid $UID --gid $GID $UNAME

# Security: no package manager leftovers
RUN rm -rf /var/lib/apt/lists/*

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Activate it
ENV PATH="/opt/venv/bin:$PATH"

# App setup
WORKDIR /app
COPY . .

# Change ownership to the non-root user
RUN chown -R $UNAME:$UNAME /app

# Set environment variables
ENV APPLICATION_VERSION=${VERSION}
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER $UNAME

# Command to run the bridge
ENTRYPOINT ["python", "-m", "src.app"]
