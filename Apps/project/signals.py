from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Task, ProjectSchedule, ProjectPhase, Milestone
import json
import logging

logger = logging.getLogger(__name__)

# Cache keys
SCHEDULE_CACHE_KEY = 'project_schedule_{}'  # Format with schedule id
PHASE_CACHE_KEY = 'project_phase_{}'  # Format with phase id
MILESTONE_CACHE_KEY = 'milestone_{}'  # Format with milestone id
PROJECT_SCHEDULE_LIST_KEY = 'project_{}_schedules'  # Format with project id
PROJECT_PHASES_KEY = 'schedule_{}_phases'  # Format with schedule id
SCHEDULE_MILESTONES_KEY = 'schedule_{}_milestones'  # Format with schedule id
PHASE_MILESTONES_KEY = 'phase_{}_milestones'  # Format with phase id

# Cache TTL in seconds (60 minutes)
CACHE_TTL = 60 * 60

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

# ProjectSchedule signals
@receiver(post_save, sender=ProjectSchedule)
def cache_schedule(sender, instance, **kwargs):
    """Cache schedule data after save"""
    try:
        schedule_data = {
            'id': instance.id,
            'project_id': instance.project_id,
            'project_title': instance.project.title,
            'estimated_start_date': instance.estimated_start_date.isoformat(),
            'estimated_end_date': instance.estimated_end_date.isoformat(),
            'description': instance.description,
            'is_baseline': instance.is_baseline,
            'progress': instance.progress,
            'created_at': instance.created_at.isoformat(),
            'updated_at': instance.updated_at.isoformat(),
        }
        
        # Cache individual schedule
        cache.set(SCHEDULE_CACHE_KEY.format(instance.id), json.dumps(schedule_data), CACHE_TTL)
        
        # Update project schedules list cache
        cache.delete(PROJECT_SCHEDULE_LIST_KEY.format(instance.project_id))
        
        logger.info(f"Cached schedule {instance.id} for project {instance.project_id}")
    except Exception as e:
        logger.error(f"Error caching schedule {instance.id}: {str(e)}")

@receiver(post_delete, sender=ProjectSchedule)
def clear_schedule_cache(sender, instance, **kwargs):
    """Clear schedule cache after delete"""
    try:
        # Delete individual schedule cache
        cache.delete(SCHEDULE_CACHE_KEY.format(instance.id))
        
        # Delete project schedules list cache
        cache.delete(PROJECT_SCHEDULE_LIST_KEY.format(instance.project_id))
        
        # Delete phases and milestones list cache
        cache.delete(PROJECT_PHASES_KEY.format(instance.id))
        cache.delete(SCHEDULE_MILESTONES_KEY.format(instance.id))
        
        logger.info(f"Cleared cache for schedule {instance.id}")
    except Exception as e:
        logger.error(f"Error clearing schedule cache {instance.id}: {str(e)}")

# ProjectPhase signals
@receiver(post_save, sender=ProjectPhase)
def cache_phase(sender, instance, **kwargs):
    """Cache phase data after save"""
    try:
        phase_data = {
            'id': instance.id,
            'schedule_id': instance.schedule_id,
            'name': instance.name,
            'description': instance.description,
            'start_date': instance.start_date.isoformat(),
            'end_date': instance.end_date.isoformat(),
            'order': instance.order,
            'is_active': instance.is_active,
            'progress': instance.progress,
            'created_at': instance.created_at.isoformat(),
            'updated_at': instance.updated_at.isoformat(),
        }
        
        # Cache individual phase
        cache.set(PHASE_CACHE_KEY.format(instance.id), json.dumps(phase_data), CACHE_TTL)
        
        # Update schedule phases list cache
        cache.delete(PROJECT_PHASES_KEY.format(instance.schedule_id))
        
        # Update schedule cache to reflect potential changes
        if instance.schedule:
            cache.delete(SCHEDULE_CACHE_KEY.format(instance.schedule_id))
        
        logger.info(f"Cached phase {instance.id} for schedule {instance.schedule_id}")
    except Exception as e:
        logger.error(f"Error caching phase {instance.id}: {str(e)}")

@receiver(post_delete, sender=ProjectPhase)
def clear_phase_cache(sender, instance, **kwargs):
    """Clear phase cache after delete"""
    try:
        # Delete individual phase cache
        cache.delete(PHASE_CACHE_KEY.format(instance.id))
        
        # Delete schedule phases list cache
        cache.delete(PROJECT_PHASES_KEY.format(instance.schedule_id))
        
        # Delete phase milestones list cache
        cache.delete(PHASE_MILESTONES_KEY.format(instance.id))
        
        # Update schedule cache to reflect changes
        if instance.schedule:
            cache.delete(SCHEDULE_CACHE_KEY.format(instance.schedule_id))
        
        logger.info(f"Cleared cache for phase {instance.id}")
    except Exception as e:
        logger.error(f"Error clearing phase cache {instance.id}: {str(e)}")

# Milestone signals
@receiver(post_save, sender=Milestone)
def cache_milestone(sender, instance, **kwargs):
    """Cache milestone data after save"""
    try:
        milestone_data = {
            'id': instance.id,
            'schedule_id': instance.schedule_id,
            'phase_id': instance.phase_id if instance.phase else None,
            'name': instance.name,
            'description': instance.description,
            'due_date': instance.due_date.isoformat(),
            'status': instance.status,
            'completion_date': instance.completion_date.isoformat() if instance.completion_date else None,
            'created_at': instance.created_at.isoformat(),
            'updated_at': instance.updated_at.isoformat(),
        }
        
        # Cache individual milestone
        cache.set(MILESTONE_CACHE_KEY.format(instance.id), json.dumps(milestone_data), CACHE_TTL)
        
        # Update schedule milestones list cache
        cache.delete(SCHEDULE_MILESTONES_KEY.format(instance.schedule_id))
        
        # Update phase milestones list cache if phase is set
        if instance.phase:
            cache.delete(PHASE_MILESTONES_KEY.format(instance.phase_id))
        
        # Update schedule and phase caches to reflect progress changes
        if instance.schedule:
            cache.delete(SCHEDULE_CACHE_KEY.format(instance.schedule_id))
        
        if instance.phase:
            cache.delete(PHASE_CACHE_KEY.format(instance.phase_id))
        
        logger.info(f"Cached milestone {instance.id} for schedule {instance.schedule_id}")
    except Exception as e:
        logger.error(f"Error caching milestone {instance.id}: {str(e)}")

@receiver(post_delete, sender=Milestone)
def clear_milestone_cache(sender, instance, **kwargs):
    """Clear milestone cache after delete"""
    try:
        # Delete individual milestone cache
        cache.delete(MILESTONE_CACHE_KEY.format(instance.id))
        
        # Delete schedule milestones list cache
        cache.delete(SCHEDULE_MILESTONES_KEY.format(instance.schedule_id))
        
        # Delete phase milestones list cache if phase is set
        if instance.phase:
            cache.delete(PHASE_MILESTONES_KEY.format(instance.phase_id))
        
        # Update schedule and phase caches to reflect changes
        if instance.schedule:
            cache.delete(SCHEDULE_CACHE_KEY.format(instance.schedule_id))
        
        if instance.phase:
            cache.delete(PHASE_CACHE_KEY.format(instance.phase_id))
        
        logger.info(f"Cleared cache for milestone {instance.id}")
    except Exception as e:
        logger.error(f"Error clearing milestone cache {instance.id}: {str(e)}") 