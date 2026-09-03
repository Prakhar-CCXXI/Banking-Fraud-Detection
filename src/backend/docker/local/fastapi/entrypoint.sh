#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -o errexit
# Treat unset variables as an error and exit immediately
set -o nounset
# Exit if any command in a pipeline fails
set -o pipefail

# Multi-line Python script to check database and message broker connectivity
python << END
import sys
import time
import socket
import os
import psycopg

maximum_wait_seconds = 30
retry_interval = 2

def check_postgres():
    try:
        psycopg.connect(
            dbname="${POSTGRES_DB}",
            user="${POSTGRES_USER}",
            password="${POSTGRES_PASSWORD}",
            host="${POSTGRES_HOST}",
            port="${POSTGRES_PORT}"
        )
        return True
    except Exception:
        return False

def check_socket(host, port):
    try:
        with socket.create_connection((host, int(port)), timeout=2):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = os.getenv("REDIS_PORT", "6379")
rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
rabbitmq_port = os.getenv("RABBITMQ_PORT", "5672")

services = [
    ("PostgreSQL", check_postgres),
    ("Redis", lambda: check_socket(redis_host, redis_port)),
    ("RabbitMQ", lambda: check_socket(rabbitmq_host, rabbitmq_port)),
]

for name, check_fn in services:
    srv_start = time.time()
    while True:
        if check_fn():
            sys.stderr.write(f"{name} is ready to accept connections\n")
            break
        if (time.time() - srv_start) > maximum_wait_seconds:
            sys.stderr.write(f"Warning: {name} connection check timed out after {maximum_wait_seconds}s\n")
            break
        time.sleep(retry_interval)
END

# Replace the current shell process with the main process (passes all arguments)
exec "$@"