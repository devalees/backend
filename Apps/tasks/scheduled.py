from celery import shared_task

@shared_task
def test_scheduled_task(*args, **kwargs):
    return "Scheduled task completed" 