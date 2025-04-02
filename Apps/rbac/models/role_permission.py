"""
Role permission model for RBAC.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from ..base import RBACModel
from django.core.exceptions import ValidationError

class RolePermission(RBACModel):
    """
    Model for storing role permissions.
    """
    role = models.ForeignKey(
        'Role',
        on_delete=models.CASCADE,
        related_name='role_permissions'
    )
    permission = models.ForeignKey(
        'RBACPermission',
        on_delete=models.CASCADE,
        related_name='role_permissions',
        null=True,
        blank=True
    )
    field_permission = models.ForeignKey(
        'FieldPermission',
        on_delete=models.CASCADE,
        related_name='role_permissions',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('role permission')
        verbose_name_plural = _('role permissions')
        unique_together = [
            ('role', 'permission'),
            ('role', 'field_permission')
        ]
        ordering = ['role', 'permission']

    def __str__(self):
        if self.permission:
            return f"{self.role} - {self.permission}"
        return f"{self.role} - {self.field_permission}"

    def clean(self):
        """Validate the role permission."""
        super().clean()
        
        # Check that either permission or field_permission is set
        if not self.permission and not self.field_permission:
            raise ValidationError(_('Either permission or field_permission must be set.'))
        
        # Check that not both permission and field_permission are set
        if self.permission and self.field_permission:
            raise ValidationError(_('Cannot set both permission and field_permission.'))
        
        # If field_permission is set, validate its content type matches the permission
        if self.field_permission and self.permission:
            if self.field_permission.content_type != self.permission.content_type:
                raise ValidationError(_('Field permission content type must match the permission content type.'))

    def get_model_class(self):
        """Get the model class from permission or field permission."""
        if self.permission:
            return self.permission.content_type.model_class()
        return self.field_permission.content_type.model_class()

    def save(self, *args, **kwargs):
        """Save the role permission."""
        self.clean()
        super().save(*args, **kwargs)
        # Invalidate permissions cache for users with this role
        from ..permissions.caching import invalidate_role_permissions
        invalidate_role_permissions(self.role, self.get_model_class())

    def delete(self, *args, **kwargs):
        """Delete the role permission."""
        # Store role and model class before deletion for cache invalidation
        role = self.role
        model_class = self.get_model_class()
        super().delete(*args, **kwargs)
        # Invalidate permissions cache for users with this role
        from ..permissions.caching import invalidate_role_permissions
        invalidate_role_permissions(role, model_class) 