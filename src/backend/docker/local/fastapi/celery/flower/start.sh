#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -o errexit
# Treat unset variables as an error and exit immediately
set -o nounset
# Exit if any command in a pipeline fails
set -o pipefail

# Define the command to start the Flower service
flower_cmd="celery \
    -A backend.app.core.celery_app \
    --broker=${CELERY_BROKER_URL} \
    flower \
    --address=0.0.0.0 \
    --port=5555 \
    --basic_auth=${CELERY_FLOWER_USER}:${CELERY_FLOWER_PASSWORD}"

# Execute watchfiles to monitor files and auto-restart Flower
exec watchfiles \
    --filter python \
    --ignore-paths '.venv,.git,__pycache__,*.pyc' \
    "$flower_cmd"