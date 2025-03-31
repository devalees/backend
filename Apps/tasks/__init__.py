from celery import shared_task

@shared_task
def test_task(*args, **kwargs):
    return "Task completed"

@shared_task
def test_task_with_retry(*args, **kwargs):
    raise Exception("Task failed") 