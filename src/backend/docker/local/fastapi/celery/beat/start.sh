#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -o errexit
# Treat unset variables as an error and exit immediately
set -o nounset
# Exit if any command in a pipeline fails
set -o pipefail

# Execute watchfiles to monitor Python files and auto-restart the Celery beat scheduler
exec watchfiles --filter python celery.__main__.main --args '-A backend.app.core.celery_app beat --loglevel=info'