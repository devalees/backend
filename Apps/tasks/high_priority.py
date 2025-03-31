from celery import shared_task

@shared_task
def test_task(*args, **kwargs):
    return "High priority task completed" 