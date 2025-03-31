# How to Use Celery in Our Project

## Quick Start Guide

### 1. Start Redis (Message Broker)
```bash
# Start Redis server
redis-server
```

### 2. Start Celery Worker
```bash
# Start Celery worker (run this in your project directory)
celery -A Server worker -l info
```

### 3. Start Celery Beat (for scheduled tasks)
```bash
# Start Celery beat in a new terminal
celery -A Server beat -l info
```

## Common Use Cases

### 1. Send Email in Background
```python
# In your views.py
from .tasks import send_email_task

def send_notification(request):
    # Instead of sending email directly
    send_email_task.delay(
        to_email='user@example.com',
        subject='Welcome!',
        body='Thank you for joining our platform.'
    )
    return JsonResponse({'message': 'Email will be sent shortly'})

# In your tasks.py
@shared_task
def send_email_task(to_email, subject, body):
    # Your email sending code here
    send_email(to_email, subject, body)
```

### 2. Process Large Files
```python
# In your views.py
from .tasks import process_file_task

def upload_file(request):
    file = request.FILES['file']
    # Save file temporarily
    file_path = save_file(file)
    # Process in background
    process_file_task.delay(file_path)
    return JsonResponse({'message': 'File processing started'})

# In your tasks.py
@shared_task
def process_file_task(file_path):
    # Process the file
    with open(file_path, 'r') as f:
        data = f.read()
    # Do something with the data
    process_data(data)
```

### 3. Schedule Daily Reports
```python
# In your celery.py
app.conf.beat_schedule = {
    'daily-report': {
        'task': 'your_app.tasks.generate_daily_report',
        'schedule': crontab(hour=9, minute=0),  # Run at 9 AM
    },
}

# In your tasks.py
@shared_task
def generate_daily_report():
    # Generate report
    report = create_report()
    # Send report
    send_report(report)
```

### 4. Handle Long-Running Tasks
```python
# In your views.py
from .tasks import process_data_task

def start_processing(request):
    # Start long-running task
    task = process_data_task.delay(large_dataset)
    return JsonResponse({
        'task_id': task.id,
        'status': 'Processing started'
    })

# In your tasks.py
@shared_task(bind=True)
def process_data_task(self, data):
    try:
        # Process data in chunks
        for chunk in data:
            process_chunk(chunk)
        return 'Processing completed'
    except Exception as e:
        # Retry on failure
        self.retry(exc=e, countdown=60)
```

### 5. Chain Multiple Tasks
```python
# In your views.py
from .tasks import process_workflow

def start_workflow(request):
    # Start workflow
    workflow = process_workflow.delay()
    return JsonResponse({
        'workflow_id': workflow.id,
        'status': 'Workflow started'
    })

# In your tasks.py
@shared_task
def process_workflow():
    return chain(
        prepare_data.s(),
        process_data.s(),
        send_notification.s()
    )()
```

## Monitoring Tasks

### 1. Check Task Status
```python
# In your views.py
def check_status(request, task_id):
    result = AsyncResult(task_id)
    return JsonResponse({
        'status': result.status,
        'result': result.result,
        'error': str(result.error) if result.error else None
    })
```

### 2. View Failed Tasks
```python
# In your views.py
def view_failed_tasks(request):
    failed_tasks = TaskResult.objects.filter(status='FAILURE')
    return JsonResponse({
        'failed_tasks': [
            {
                'task_id': task.task_id,
                'error': task.error,
                'date': task.date_created
            }
            for task in failed_tasks
        ]
    })
```

## Common Commands

```bash
# Start worker
celery -A Server worker -l info

# Start beat
celery -A Server beat -l info

# Check worker status
celery -A Server status

# View active tasks
celery -A Server inspect active

# Clear all tasks
celery -A Server purge
```

## Tips and Best Practices

1. **Always Use .delay() or .apply_async()**
   ```python
   # Good
   task.delay(arg1, arg2)
   
   # Bad
   task(arg1, arg2)  # This runs synchronously!
   ```

2. **Handle Task Failures**
   ```python
   @shared_task(bind=True)
   def safe_task(self):
       try:
           # Your code here
           result = do_something()
           return result
       except Exception as e:
           # Log error
           logger.error(f"Task failed: {str(e)}")
           # Retry
           self.retry(exc=e)
   ```

3. **Use Task Timeouts**
   ```python
   @shared_task(time_limit=300)  # 5 minutes timeout
   def long_task():
       # Your code here
       pass
   ```

4. **Monitor Task Progress**
   ```python
   @shared_task(bind=True)
   def progress_task(self):
       total = 100
       for i in range(total):
           # Update progress
           self.update_state(
               state='PROGRESS',
               meta={'current': i, 'total': total}
           )
           # Do work
           time.sleep(1)
   ```

Remember:
- Always test tasks thoroughly
- Monitor task execution
- Handle errors gracefully
- Use appropriate timeouts
- Keep tasks focused and small 

## Visualizing Celery Tasks

### 1. Flower - Real-time Celery Monitoring
Flower is the most popular web-based monitoring tool for Celery.

```bash
# Install Flower
pip install flower

# Start Flower (run this in your project directory)
celery -A Server flower
```

Access Flower at `http://localhost:5555`

Features:
- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Task graphs and charts
- Rate limiting and control

### 2. Django Celery Results Admin
We already have django-celery-results installed. Access it through Django admin:

```python
# In your admin.py
from django_celery_results.models import TaskResult

@admin.register(TaskResult)
class TaskResultAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'task_name', 'status', 'date_created', 'date_done')
    list_filter = ('status', 'date_created', 'date_done')
    search_fields = ('task_id', 'task_name', 'status')
    readonly_fields = ('date_created', 'date_done', 'result', 'meta')
```

### 3. Custom Dashboard Example
Create a simple dashboard to monitor tasks:

```python
# In your views.py
from django_celery_results.models import TaskResult
from celery.result import AsyncResult

def task_dashboard(request):
    # Get recent tasks
    recent_tasks = TaskResult.objects.order_by('-date_created')[:10]
    
    # Get task statistics
    stats = {
        'total': TaskResult.objects.count(),
        'success': TaskResult.objects.filter(status='SUCCESS').count(),
        'failure': TaskResult.objects.filter(status='FAILURE').count(),
        'pending': TaskResult.objects.filter(status='PENDING').count(),
    }
    
    return render(request, 'tasks/dashboard.html', {
        'recent_tasks': recent_tasks,
        'stats': stats
    })

# In your templates/tasks/dashboard.html
{% extends 'base.html' %}

{% block content %}
<div class="dashboard">
    <h2>Task Statistics</h2>
    <div class="stats">
        <div class="stat-box">
            <h3>Total Tasks</h3>
            <p>{{ stats.total }}</p>
        </div>
        <div class="stat-box success">
            <h3>Success</h3>
            <p>{{ stats.success }}</p>
        </div>
        <div class="stat-box failure">
            <h3>Failed</h3>
            <p>{{ stats.failure }}</p>
        </div>
        <div class="stat-box pending">
            <h3>Pending</h3>
            <p>{{ stats.pending }}</p>
        </div>
    </div>

    <h2>Recent Tasks</h2>
    <table>
        <thead>
            <tr>
                <th>Task ID</th>
                <th>Name</th>
                <th>Status</th>
                <th>Created</th>
                <th>Completed</th>
            </tr>
        </thead>
        <tbody>
            {% for task in recent_tasks %}
            <tr>
                <td>{{ task.task_id }}</td>
                <td>{{ task.task_name }}</td>
                <td class="status-{{ task.status.lower }}">{{ task.status }}</td>
                <td>{{ task.date_created }}</td>
                <td>{{ task.date_done|default:"-" }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

### 4. Real-time Task Progress Updates
Use WebSockets to show real-time task progress:

```python
# In your tasks.py
@shared_task(bind=True)
def long_task(self):
    total = 100
    for i in range(total):
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={
                'current': i,
                'total': total,
                'percent': round((i / total) * 100, 2)
            }
        )
        time.sleep(1)
    return 'Task completed!'

# In your views.py
from django.http import JsonResponse
from celery.result import AsyncResult

def get_task_progress(request, task_id):
    task_result = AsyncResult(task_id)
    if task_result.state == 'PROGRESS':
        return JsonResponse({
            'state': task_result.state,
            'progress': task_result.info
        })
    return JsonResponse({
        'state': task_result.state,
        'result': task_result.result
    })
```

### 5. Task Monitoring Best Practices

1. **Set Up Alerts**
```python
# In your tasks.py
@shared_task(bind=True)
def monitored_task(self):
    try:
        # Your task code here
        result = do_something()
        return result
    except Exception as e:
        # Send alert on failure
        send_alert(
            f"Task {self.request.id} failed: {str(e)}",
            level="error"
        )
        raise
```

2. **Track Task Duration**
```python
@shared_task(bind=True)
def timed_task(self):
    start_time = time.time()
    try:
        result = do_something()
        duration = time.time() - start_time
        if duration > 300:  # More than 5 minutes
            send_alert(
                f"Task {self.request.id} took {duration:.2f} seconds",
                level="warning"
            )
        return result
    except Exception as e:
        duration = time.time() - start_time
        send_alert(
            f"Task {self.request.id} failed after {duration:.2f} seconds",
            level="error"
        )
        raise
```

3. **Monitor Resource Usage**
```python
@shared_task(bind=True)
def resource_monitored_task(self):
    import psutil
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    try:
        result = do_something()
        final_memory = process.memory_info().rss
        memory_used = final_memory - initial_memory
        
        if memory_used > 100 * 1024 * 1024:  # More than 100MB
            send_alert(
                f"Task {self.request.id} used {memory_used/1024/1024:.2f}MB",
                level="warning"
            )
        return result
    except Exception as e:
        send_alert(
            f"Task {self.request.id} failed: {str(e)}",
            level="error"
        )
        raise
```

Remember:
- Use Flower for real-time monitoring
- Set up proper alerts for failures
- Track task duration and resource usage
- Keep monitoring data for analysis
- Set up proper logging for debugging 

## API Endpoints for Task Management

### TaskAwareModelViewSet Endpoints

The `TaskAwareModelViewSet` provides endpoints for processing models using Celery tasks:

```python
# Process a single instance
POST /api/{model_name}/process/
{
    "kwargs": {
        "param1": "value1",
        "param2": "value2"
    }
}

# Process multiple instances
POST /api/{model_name}/process_batch/
{
    "instance_ids": [1, 2, 3],
    "kwargs": {
        "param1": "value1",
        "param2": "value2"
    }
}

# Get task status
GET /api/{model_name}/{id}/task_status/
```

### Project Task Endpoints

The `TaskViewSet` provides endpoints for managing project tasks:

```python
# Assign task to user
POST /api/tasks/{id}/assign/
{
    "user_id": 123
}

# Change task status
POST /api/tasks/{id}/change_status/
{
    "status": "in_progress"
}
```

### Task Configuration

Tasks can be configured using the `TaskConfig` model:

```python
class MyModel(TaskAwareModel):
    task_config = TaskConfig(
        max_retries=3,
        retry_delay=60,
        timeout=300,
        priority=1,
        queue='high_priority'
    )
```

### Task Status Tracking

Tasks automatically track their status and provide properties for checking state:

```python
# Check task status
if instance.is_processing:
    print("Task is running")
elif instance.is_completed:
    print("Task completed successfully")
elif instance.is_failed:
    print(f"Task failed: {instance.error_message}")
```

### Task Results

Task results are stored in the model instance:

```python
# Store task result
instance.task_result = {
    'processed': True,
    'timestamp': timezone.now().isoformat(),
    'data': processed_data
}
instance.save()

# Access task result
result = instance.task_result
```

### Error Handling

Tasks automatically handle errors and retries:

```python
# Task with retry logic
@shared_task(bind=True, max_retries=3)
def my_task(self):
    try:
        # Task logic here
        pass
    except Exception as e:
        # Retry the task
        self.retry(exc=e, countdown=60)
```

### Task Monitoring

Monitor task execution using Celery signals:

```python
from celery import signals

@signals.task_sent.connect
def task_sent_handler(sender=None, task_id=None, **kwargs):
    print(f"Task {task_id} sent")

@signals.task_received.connect
def task_received_handler(sender=None, request=None, **kwargs):
    print(f"Task {request.id} received")

@signals.task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    print(f"Task {sender.request.id} succeeded")

@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    print(f"Task {task_id} failed: {str(exception)}")
``` 