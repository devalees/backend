from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import ImportExportLog


@receiver(pre_save, sender=ImportExportLog)
def update_failed_records(sender, instance, **kwargs):
    """Update failed records count before saving."""
    if instance.records_processed is not None and instance.records_succeeded is not None:
        instance.records_failed = instance.records_processed - instance.records_succeeded 