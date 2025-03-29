from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Task

@receiver(pre_save, sender=Task)
def update_parent_task_status(sender, instance, **kwargs):
    """Update parent task status based on subtasks"""
    if instance.parent_task:
        # Get all sibling tasks (including this one if it exists)
        sibling_tasks = Task.objects.filter(parent_task=instance.parent_task)
        if instance.pk:  # If task exists
            sibling_tasks = sibling_tasks.exclude(pk=instance.pk)
        
        # If all sibling tasks are done and this task is done
        if (not sibling_tasks.exclude(status=Task.Status.DONE).exists() and 
            instance.status == Task.Status.DONE):
            instance.parent_task.status = Task.Status.DONE
            instance.parent_task.save()
        # If any task is in progress
        elif (sibling_tasks.filter(status=Task.Status.IN_PROGRESS).exists() or 
              instance.status == Task.Status.IN_PROGRESS):
            instance.parent_task.status = Task.Status.IN_PROGRESS
            instance.parent_task.save()
        # If all tasks are todo
        elif (not sibling_tasks.exclude(status=Task.Status.TODO).exists() and 
              instance.status == Task.Status.TODO):
            instance.parent_task.status = Task.Status.TODO
            instance.parent_task.save() 