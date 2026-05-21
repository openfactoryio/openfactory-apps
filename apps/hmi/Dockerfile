# ------------------------------------------------------------------------------
# 🐳 Dockerfile for CNC HMI App
#
# build:
#   docker build -f Dockerfile -t cnc-hmi-app .
#
#   docker run --rm -it --user 1234:5678 cnc-hmi-app bash
# ------------------------------------------------------------------------------

# ---- builder stage ----
FROM python:3.12-slim AS builder

# Argument for version management
ARG OPENFACTORY_VERSION=main

# Install git
RUN apt-get update && apt-get install -y git

# Create virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
       "openfactory[flask] @ git+https://github.com/openfactoryio/openfactory-core.git@${OPENFACTORY_VERSION}" \
    && pip install -r requirements.txt

# ---- final stage ----
FROM python:3.12-slim

# Arguments for non-root user creation
ARG UNAME=cnc-hmi
ARG USER_UID=1200
ARG USER_GID=1200

# Argument for version management
ARG VERSION=dev

# Create runtime user/group
RUN groupadd --gid $USER_GID $UNAME \
    && useradd --create-home --uid $USER_UID --gid $USER_GID $UNAME

# Create mountpoints
RUN mkdir /mnt/instance
RUN mkdir /mnt/nc_files

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

# Run
CMD ["python", "-m", "src.hmi"]
