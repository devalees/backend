# How To Use Celery in Our Project

## Table of Contents
1. [What is Celery?](#what-is-celery)
2. [Basic Setup](#basic-setup)
3. [Creating Tasks](#creating-tasks)
4. [Running Tasks](#running-tasks)
5. [Task Scheduling](#task-scheduling)
6. [Task Monitoring](#task-monitoring)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

## What is Celery?

Celery is a task queue system that helps you run background tasks in your Django application. Think of it like a to-do list for your computer - instead of doing everything right away, some tasks can be done later in the background.

### Why Use Celery?
- Handle long-running tasks without making users wait
- Schedule tasks to run at specific times
- Process tasks in parallel
- Handle failed tasks gracefully
- Scale your application easily

## Basic Setup

### 1. Install Required Packages
```bash
pip install celery django-celery-beat django-celery-results redis
```

### 2. Add to Django Settings
In your `settings.py`:
```python
INSTALLED_APPS = [
    ...
    'django_celery_beat',
    'django_celery_results',
]

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'
CELERY_TIMEZONE = 'UTC'  # Change to your timezone
```

### 3. Create Celery Configuration
In your project's `__init__.py`:
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

Create `celery.py` in your project folder:
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

app = Celery('your_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

## Creating Tasks

### 1. Basic Task
```python
from celery import shared_task

@shared_task
def add(x, y):
    return x + y
```

### 2. Task with Retry
```python
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

@shared_task(bind=True, max_retries=3)
def process_data(self, data):
    try:
        # Your processing code here
        result = process_something(data)
        return result
    except Exception as e:
        # Retry the task if it fails
        self.retry(exc=e, countdown=60)  # Wait 60 seconds before retrying
```

### 3. Task with Progress Tracking
```python
from celery import shared_task
from celery_progress.backend import ProgressRecorder

@shared_task(bind=True)
def long_running_task(self):
    progress_recorder = ProgressRecorder(self)
    total = 100
    
    for i in range(total):
        # Do something
        progress_recorder.set_progress(i + 1, total)
    
    return 'Task completed!'
```

## Running Tasks

### 1. Run Task Immediately
```python
# In your views or other code
from .tasks import add

# Run task asynchronously
result = add.delay(4, 4)  # Returns a task ID

# Get the result
print(result.get())  # Will print 8
```

### 2. Run Task with Arguments
```python
@shared_task
def send_email(to_email, subject, body):
    # Send email code here
    pass

# Run the task
send_email.delay('user@example.com', 'Hello', 'This is a test email')
```

## Task Scheduling

### 1. Schedule a Task
```python
from celery.schedules import crontab

# In your celery.py
app.conf.beat_schedule = {
    'cleanup-old-data': {
        'task': 'your_app.tasks.cleanup_old_data',
        'schedule': crontab(hour=0, minute=0),  # Run at midnight
    },
    'send-daily-report': {
        'task': 'your_app.tasks.send_daily_report',
        'schedule': crontab(hour=9, minute=0),  # Run at 9 AM
    },
}
```

### 2. Dynamic Scheduling
```python
from django_celery_beat.models import PeriodicTask, IntervalSchedule

# Create a schedule
schedule, created = IntervalSchedule.objects.get_or_create(
    every=1,
    period=IntervalSchedule.HOURS,
)

# Create a periodic task
PeriodicTask.objects.create(
    name='Hourly cleanup',
    task='your_app.tasks.cleanup_data',
    interval=schedule
)
```

## Task Monitoring

### 1. View Task Results
```python
from django_celery_results.models import TaskResult

# Get all completed tasks
completed_tasks = TaskResult.objects.filter(status='SUCCESS')

# Get failed tasks
failed_tasks = TaskResult.objects.filter(status='FAILURE')
```

### 2. Monitor Task Status
```python
# In your view
def check_task_status(request, task_id):
    task_result = TaskResult.objects.get(task_id=task_id)
    return JsonResponse({
        'status': task_result.status,
        'result': task_result.result,
        'error': task_result.error
    })
```

## Common Patterns

### 1. Chaining Tasks
```python
from celery import chain

def process_workflow():
    return chain(
        task1.s(),
        task2.s(),
        task3.s()
    )()
```

### 2. Grouping Tasks
```python
from celery import group

def process_multiple_items(items):
    return group(
        process_item.s(item) for item in items
    )()
```

### 3. Error Handling
```python
@shared_task(bind=True)
def safe_task(self):
    try:
        # Your code here
        result = do_something()
        return result
    except Exception as e:
        # Log the error
        logger.error(f"Task failed: {str(e)}")
        # Retry or handle the error
        self.retry(exc=e)
```

## Troubleshooting

### Common Issues and Solutions

1. **Task Not Running**
   - Check if Celery worker is running
   - Verify broker connection
   - Check task registration

2. **Tasks Stuck in Queue**
   - Check worker processes
   - Verify broker connection
   - Check task timeouts

3. **Memory Issues**
   - Monitor worker memory usage
   - Adjust worker settings
   - Use task timeouts

### Useful Commands

```bash
# Start Celery worker
celery -A your_project worker -l info

# Start Celery beat (for scheduled tasks)
celery -A your_project beat -l info

# Check worker status
celery -A your_project status

# Inspect active tasks
celery -A your_project inspect active

# Clear all tasks
celery -A your_project purge
```

### Best Practices

1. **Task Design**
   - Keep tasks small and focused
   - Use meaningful task names
   - Include proper error handling

2. **Performance**
   - Use task timeouts
   - Implement retry mechanisms
   - Monitor task execution time

3. **Monitoring**
   - Set up proper logging
   - Monitor task results
   - Track failed tasks

4. **Security**
   - Validate task inputs
   - Use proper permissions
   - Secure sensitive data

Remember: Always test your tasks thoroughly before deploying to production! 