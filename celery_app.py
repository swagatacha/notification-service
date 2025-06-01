from celery import Celery
from celery.schedules import crontab
from commons import config  # Make sure this has access to your config
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Define the Celery instance
celery_app = Celery(
    'notification_service',  # Name of your app
    broker=f'redis://{config.redis["host"]}:{config.redis["port"]}',  # Celery broker URL from the config
    backend=None  # Where to store results, can be Redis, Database, etc.
)

celery_app.conf.task_ignore_result = True
# Automatically discover tasks in all apps (optional)
celery_app.autodiscover_tasks(['scripts'])
# import scripts.cleanup_logs
# import scripts.pending_order_state_checker


celery_app.conf.beat_schedule = {
    'cleanup_logs_every_24_hours': {
        'task': 'scripts.cleanup_logs.cleanup_logs_task',  # Path to your task
        "schedule": crontab(minute="*/30"),  # Runs every day at midnight
    },
    'check-pending-orders-every-5-minutes': {
        'task': 'scripts.pending_order_state_checker.scan_and_process',
        "schedule": crontab(minute="*/30"),
    },
    'change-service-providers-every-hours': {
        'task': 'scripts.provider_change.provider_change_task',
        "schedule": crontab(minute=0),
    },
}

celery_app.conf.timezone = 'UTC'