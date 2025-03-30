import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')

# Create the Celery app
app = Celery('Core')

# Configure Celery using Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered Django app configs
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Configure task routing
app.conf.task_routes = {
    'Apps.*.tasks.*': {'queue': 'default'},
}

# Configure task serialization
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# Configure task result backend
app.conf.result_backend = 'django-db'

# Configure task time limits
app.conf.task_time_limit = 60 * 60  # 1 hour
app.conf.task_soft_time_limit = 50 * 60  # 50 minutes

# Configure task retry settings
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

@app.task(bind=True)
def debug_task(self):
    """Task for debugging purposes"""
    print(f'Request: {self.request!r}') 