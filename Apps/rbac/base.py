"""
Base RBAC model with permission checking functionality.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()

class RBACModel(models.Model):
    """
    Base model class for RBAC models.
    """
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('When the object was created.')
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('When the object was last updated.')
    )
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        help_text=_('User who created the object.')
    )
    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        help_text=_('User who last updated the object.')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether the object is active.')
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return str(self.id)

    def clean(self):
        """
        Validate the model.
        """
        # Skip created_by validation for permission models during permission generation
        if self._meta.model_name in ['rbacpermission', 'fieldpermission', 'rolepermission', 'userrole']:
            return
        
        if not self.pk and not self.created_by:
            raise ValidationError(_('Created by user is required.'))

    def save(self, *args, **kwargs):
        """
        Save the model.
        """
        user = kwargs.pop('user', None)
        if not self.created_by and self.pk is None:
            self.created_by = user
        if self.pk:
            self.updated_by = user
            self.updated_at = timezone.now()
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        """
        Soft delete the object by setting is_active to False.
        """
        self.is_active = False
        self.updated_by = user
        self.save(user=user)

    def restore(self, user=None):
        """
        Restore the object by setting is_active to True.
        """
        self.is_active = True
        self.updated_by = user
        self.save(user=user)

    def can_view(self, user):
        """Check if user can view this object."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user == self.created_by

    def can_add(self, user):
        """Check if user can add objects of this type."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return True  # Allow authenticated users to add objects

    def can_change(self, user):
        """Check if user can change this object."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user == self.created_by

    def can_delete(self, user):
        """Check if user can delete this object."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user == self.created_by

    def check_permission(self, user, action):
        """Check if user has permission for the given action."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if action == 'view':
            return self.can_view(user)
        elif action == 'add':
            return self.can_add(user)
        elif action == 'change':
            return self.can_change(user)
        elif action == 'delete':
            return self.can_delete(user)
        return False

    def get_accessible_fields(self, user):
        """Get fields that the user can access."""
        if not user.is_authenticated:
            return {}
        if user.is_superuser:
            return {field.name: {'view', 'add', 'change'} for field in self._meta.fields}
        if user == self.created_by:
            return {field.name: {'view', 'add', 'change'} for field in self._meta.fields}
        return {}

    @classmethod
    def get_queryset_for_user(cls, user):
        """Get queryset of objects accessible to the user."""
        if not user.is_authenticated:
            return cls.objects.none()
        if user.is_superuser:
            return cls.objects.all()
        return cls.objects.filter(created_by=user)

    def _get_current_user(self):
        """Get the current user from the request."""
        from django.core.exceptions import ValidationError
        try:
            from django.core.handlers.wsgi import WSGIRequest
            from django.conf import settings
            request = getattr(settings, 'CURRENT_REQUEST', None)
            if request and isinstance(request, WSGIRequest):
                return request.user
        except Exception:
            pass
        return None

@receiver(post_migrate)
def create_permissions(sender, **kwargs):
    """
    Create permissions for all RBAC models after migrations.
    """
    from django.apps import apps
    from .permissions.generation import generate_permissions

    # Get all models that inherit from RBACModel
    for model in apps.get_models():
        if issubclass(model, RBACModel) and model is not RBACModel:
            generate_permissions(model) 