ARG PYTHON_VERSION=3.13.1

FROM python:${PYTHON_VERSION}-slim-bookworm AS python

# Stage-1 : build dependency wheels
FROM python AS python-build-stage

RUN apt-get update && apt-get install \
  --no-install-recommends -y \
  build-essential \
  libpq-dev

COPY ./backend/requirements.txt .

RUN pip wheel --wheel-dir /usr/src/app/wheels \
    -r requirements.txt \
    --no-cache-dir

# Stage 2: Python run stage
FROM python as python-run-stage

# Define application arguments
ARG APP_HOME=/src
ARG APP_USER=fastapi
ARG APP_GROUP=fastapi

# Set environment variables to prevent bytecode and buffering
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR ${APP_HOME}

# Install system dependencies and clean up unused files
RUN apt-get update && apt-get install --no-install-recommends -y \
    sudo git bash-completion nano ssh gettext \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# Implement security best practices by creating a non-root user and group
RUN groupadd -r ${APP_GROUP} && \
    useradd -r -g ${APP_GROUP} -d ${APP_HOME} -m ${APP_USER}

# Create the logs directory and set the appropriate permissions
RUN mkdir -p ${APP_HOME}/backend/app/logs && \
    chown -R ${APP_USER}:${APP_GROUP} ${APP_HOME}/backend/app/logs && \
    chmod 775 ${APP_HOME}/backend/app/logs

# Copy the Python dependency wheels from the previous build stage
COPY --from=python-build-stage /usr/src/app/wheels /wheels

# Install Python dependencies via pip using the pre-compiled wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
    && rm -rf /wheels/

# Copy the entrypoint and start scripts and set ownership to the fastapi user and group
COPY --chown=${APP_USER}:${APP_GROUP} ./backend/docker/local/fastapi/entrypoint.sh /entrypoint.sh
COPY --chown=${APP_USER}:${APP_GROUP} ./backend/docker/local/fastapi/start.sh /start.sh

# Convert Windows-style line endings to Unix-style line endings
RUN sed -i 's/\r$//g' /entrypoint.sh /start.sh

# Make the entrypoint and start shell scripts executable
RUN chmod +x /entrypoint.sh /start.sh

# Copy application files from the host machine to the container's working directory
COPY --chown=${APP_USER}:${APP_GROUP} . ${APP_HOME}

# Set the user that will run the container and subsequent commands
USER ${APP_USER}

# Define the executable that will run when the container starts
ENTRYPOINT ["/entrypoint.sh"]




# Key Configurations Explained:

# Aliases and Environment: Uses FROM python under the alias python-run-stage and defines arguments for the app directory, user, and group. It also sets PYTHONDONTWRITEBYTECODE=1 to stop Python from writing .pyc files, and PYTHONUNBUFFERED=1 to allow real-time console output.  
# TXT
# + 1

# System Dependencies: Uses apt-get to install necessary packages (like sudo, git, nano, ssh, and gettext), followed by an aggressive purge of unused packages and the package cache to keep the image lightweight.  
# TXT

# Security Restrictions: Replaces the default root user by executing groupadd and useradd to create a dedicated fastapi system user with minimal required permissions.  
# TXT

# Log Configurations: Creates the /src/backend/app/logs folder and assigns 775 permissions to allow the owner/group full access for maintenance, while others only have read/execute rights.  
# TXT

# Multi-Stage Asset Copy: Successfully uses the --from flag to securely pull over the pre-compiled .whl dependencies from the previous python-build-stage.  
# TXT


