#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -o errexit
# Treat unset variables as an error and exit immediately
set -o nounset
# Exit if any command in a pipeline fails
set -o pipefail

# Multi-line Python script to check database connectivity
python << END
import sys
import time
import psycopg

maximum_wait_seconds = 30
retry_interval = 5
start_time = time.time()

def check_database():
    try:
        psycopg.connect(
            dbname="${POSTGRES_DB}",
            user="${POSTGRES_USER}",
            password="${POSTGRES_PASSWORD}",
            host="${POSTGRES_HOST}",
            port="${POSTGRES_PORT}"
        )
        return True
    except psycopg.OperationalError as error:
        elapsed = int(time.time() - start_time)
        sys.stderr.write(f"Database connection attempt failed after {elapsed} seconds. {error}\n")
        return False

while True:
    if check_database():
        break
    if (time.time() - start_time) > maximum_wait_seconds:
        sys.stderr.write(f"Error: Database connection could not be established after {maximum_wait_seconds} seconds\n")
        sys.exit(1)
    
    sys.stderr.write(f"Waiting {retry_interval} seconds before retrying\n")
    time.sleep(retry_interval)
END

# Redirect output to standard error and print success message
>&2 echo 'PostgreSQL is ready to accept connections'

# Replace the current shell process with the main process (passes all arguments)
exec "$@"