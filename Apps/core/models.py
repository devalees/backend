from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver
from Apps.data_import_export.mixins import ImportExportMixin

User = get_user_model()

class BaseModel(ImportExportMixin, models.Model):
    """Base model with common fields and methods"""
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    # Import/Export configuration
    import_export_enabled = True  # Enable import/export by default for all models
    import_export_fields = None  # Use all non-relation fields by default

    def clean(self):
        """Base validation method"""
        pass

    def save(self, *args, **kwargs):
        """Save the model with validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, hard=False, *args, **kwargs):
        """
        Soft delete the object by setting is_active to False.
        If hard is True, perform a hard delete.
        """
        if hard:
            super().delete(*args, **kwargs)
        else:
            self.is_active = False
            self.save()

    def hard_delete(self):
        """Hard delete the object"""
        models.Model.delete(self)

def get_current_user():
    """Get the current user from the thread local storage"""
    from threading import local
    _thread_locals = local()
    return getattr(_thread_locals, 'user', None)

def set_current_user(user):
    """Set the current user in the thread local storage"""
    from threading import local
    _thread_locals = local()
    _thread_locals.user = user

@receiver(pre_save)
def set_user_fields(sender, instance, **kwargs):
    """Set created_by and updated_by fields before saving"""
    if not isinstance(instance, BaseModel):
        return

    user = get_current_user()
    if user and user.is_authenticated:
        if not instance.pk:  # New instance
            instance.created_by = user
        instance.updated_by = user 