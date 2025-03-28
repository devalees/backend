from django.db import models
from django.apps import apps
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your models here.

class FieldControl(models.Model):
    field_name = models.CharField(max_length=100, help_text="Name of the field", default='default_field')
    module_id = models.CharField(max_length=50, help_text="Model identifier (e.g., 'users.User')")
    field_type = models.CharField(max_length=50, help_text="Type of the field", default='CharField')
    is_active = models.BooleanField(default=True, help_text="Whether this field is active")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_field_controls')
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Field'
        verbose_name_plural = 'Fields'
        ordering = ['module_id', 'field_name']
        unique_together = ['module_id', 'field_name']

    def __str__(self):
        return f"{self.field_name} ({self.module_id})"

    def get_model(self):
        """Get the actual model class this field belongs to"""
        try:
            app_label, model_name = self.module_id.split('.')
            return apps.get_model(app_label, model_name)
        except (ValueError, LookupError):
            return None

    def clean(self):
        """Validate the model exists"""
        model = self.get_model()
        if not model:
            raise ValidationError({'module_id': 'Invalid model identifier. Format should be "app_label.ModelName"'})
        
        # Validate field exists in model
        try:
            field = model._meta.get_field(self.field_name)
            self.field_type = field.get_internal_type()
        except:
            raise ValidationError({'field_name': f'Field {self.field_name} does not exist in model {self.module_id}'})

@receiver(post_migrate)
def create_field_controls(sender, **kwargs):
    """
    Create FieldControl entries for all fields in all models after migrations.
    This ensures new fields are automatically tracked.
    """
    # Skip for contenttypes and auth migrations
    if sender.name in ['contenttypes', 'auth', 'admin', 'sessions']:
        return

    for model in apps.get_models():
        # Skip abstract models and models from excluded apps
        if model._meta.abstract or model._meta.app_label in ['contenttypes', 'auth', 'admin', 'sessions']:
            continue

        module_id = f"{model._meta.app_label}.{model._meta.model_name}"
        
        # Create entries for each field
        for field in model._meta.get_fields():
            # Skip reverse relations and many-to-many relationships
            if field.is_relation and not (field.one_to_one or field.many_to_one):
                continue

            # Create or update field control
            field_control, created = FieldControl.objects.get_or_create(
                module_id=module_id,
                field_name=field.name,
                defaults={
                    'field_type': field.get_internal_type(),
                    'is_active': True
                }
            )
