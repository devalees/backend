"""
Role Permission model for RBAC.
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .role import Role
from .permission import RBACPermission, FieldPermission
from ..utils.cache import invalidate_permissions_cache
from .base import RBACModel

class RolePermission(RBACModel):
    """Model for role permissions."""
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        help_text=_('The role this permission belongs to.')
    )
    permission = models.ForeignKey(
        RBACPermission,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        null=True,
        blank=True,
        help_text=_('The permission assigned to the role.')
    )
    field_permission = models.ForeignKey(
        FieldPermission,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        null=True,
        blank=True,
        help_text=_('The field permission assigned to the role.')
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this role permission is active.')
    )

    class Meta:
        """Meta options."""
        verbose_name = _('Role Permission')
        verbose_name_plural = _('Role Permissions')
        unique_together = [
            ('role', 'permission'),
            ('role', 'field_permission')
        ]
        ordering = ['role', 'permission', 'field_permission']

    def __str__(self):
        """String representation."""
        if self.permission:
            return f'{self.role} - {self.permission}'
        return f'{self.role} - {self.field_permission}'

    def clean(self):
        """Validate the model."""
        if not self.permission and not self.field_permission:
            raise ValidationError(_('Either permission or field_permission must be set.'))
        if self.permission and self.field_permission:
            raise ValidationError(_('Cannot set both permission and field_permission.'))

    def save(self, *args, **kwargs):
        """Save the model."""
        self.clean()
        super().save(*args, **kwargs)
        # Invalidate permissions cache for users with this role
        invalidate_permissions_cache(self.role)

    def delete(self, *args, **kwargs):
        """Delete the model."""
        # Invalidate permissions cache for users with this role
        invalidate_permissions_cache(self.role)
        super().delete(*args, **kwargs) 