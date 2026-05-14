FROM python:3.12-slim

# Build arguments
ARG UNAME=hmi
ARG USER_ID=1002
ARG GROUP_ID=1002

# Arguments for version management
ARG VERSION=dev
ARG OFA_VERSION=main

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install git and create a non-root user and group

RUN apt-get update && apt-get install -y git \
    && groupadd --gid ${GROUP_ID} ${UNAME} \
    && useradd --create-home --uid ${USER_ID} --gid ${GROUP_ID} ${UNAME} \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application code
RUN mkdir hmi
COPY . hmi

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r hmi/requirements.txt

RUN pip install --no-cache-dir \
    "openfactory[flask] @ git+https://github.com/openfactoryio/openfactory-core.git@${OFA_VERSION}"

# Change ownership to the non-root user
RUN chown -R $UNAME:$UNAME /app

# Set environment variables
ENV APPLICATION_VERSION=${VERSION}
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER $UNAME

CMD ["flask", "run", "--debug"]
