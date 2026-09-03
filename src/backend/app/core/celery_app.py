import os
import importlib.util
from celery import Celery
from backend.app.core.config import settings

broker_url = (
    settings.CELERY_BROKER_URL
    if settings.CELERY_BROKER_URL
    else f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}//"
)
result_backend = (
    settings.CELERY_RESULT_BACKEND
    if settings.CELERY_RESULT_BACKEND
    else f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
)

# Create the Celery instance with RabbitMQ as the broker and Redis as the backend
celery_app = Celery(
    "worker",
    broker=broker_url,
    backend=result_backend,
)

# Update the Celery app configuration
celery_app.conf.update(
    broker_heartbeat=30,
    broker_pool_limit=10,
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    task_track_started=True,
    result_serializer="json",
    accept_content=["application/json"],
    result_backend_max_retries=10,
    task_send_sent_event=True,
    result_extended=True,
    result_backend_always_retry=True,
    result_expires=3600,
    task_time_limit=5 * 60,
    task_soft_time_limit=5 * 60,
    worker_send_task_events=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=300,
    task_max_retries=3,
    task_default_queue="nextgen_tasks",
    task_create_missing_queues=True,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=50000,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
)

# Safely discover tasks if package exists
packages_to_discover = []
if importlib.util.find_spec("backend.app.core.emails") is not None:
    packages_to_discover.append("backend.app.core.emails")

if packages_to_discover:
    celery_app.autodiscover_tasks(
        packages=packages_to_discover,
        related_name="tasks",
        force=True,
    )
