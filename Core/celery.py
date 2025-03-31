import os
from celery import Celery
from django.conf import settings
from celery.signals import task_sent, task_received, task_postrun, task_failure
from celery.utils.log import get_task_logger
import logging

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')

# Configure logging
logger = logging.getLogger(__name__)

# Create the Celery app
app = Celery('Core')

# Configure Celery using Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered Django app configs
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Configure task routing
app.conf.task_routes = settings.CELERY_TASK_ROUTES

# Configure task serialization
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# Configure task result backend
app.conf.result_backend = settings.CELERY_RESULT_BACKEND

# Configure task time limits
app.conf.task_time_limit = settings.CELERY_TASK_TIME_LIMIT
app.conf.task_soft_time_limit = settings.CELERY_TASK_SOFT_TIME_LIMIT

# Configure task retry settings
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

# Configure worker settings
app.conf.worker_concurrency = settings.CELERY_WORKER_CONCURRENCY
app.conf.worker_max_tasks_per_child = settings.CELERY_WORKER_MAX_TASKS_PER_CHILD
app.conf.worker_prefetch_multiplier = settings.CELERY_WORKER_PREFETCH_MULTIPLIER
app.conf.worker_send_task_events = settings.CELERY_WORKER_SEND_TASK_EVENTS

# Configure Celery app
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='django-db',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue='default',
    task_queues={
        'high_priority': {
            'exchange': 'high_priority',
            'routing_key': 'high_priority',
            'queue_arguments': {'x-max-priority': 10},
        },
        'low_priority': {
            'exchange': 'low_priority',
            'routing_key': 'low_priority',
            'queue_arguments': {'x-max-priority': 1},
        },
    },
    task_routes={
        'Apps.tasks.high_priority.*': {'queue': 'high_priority'},
        'Apps.tasks.low_priority.*': {'queue': 'low_priority'},
    },
)

# Set up task monitoring
logger = get_task_logger(__name__)

@task_sent.connect
def task_sent_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    logger.info(f"Task {task_id} sent to queue")

@task_received.connect
def task_received_handler(sender=None, request=None, **kwds):
    logger.info(f"Task {request.id} received by worker")

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **kwds):
    logger.info(f"Task {task_id} completed successfully")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, **kwds):
    logger.error(f"Task {task_id} failed with error: {str(exception)}")

# Register signal handlers with the app
app.task_sent_handler = task_sent_handler
app.task_received_handler = task_received_handler
app.task_postrun_handler = task_postrun_handler
app.task_failure_handler = task_failure_handler

@app.task(bind=True)
def debug_task(self):
    """Task for debugging purposes"""
    print(f'Request: {self.request!r}') 