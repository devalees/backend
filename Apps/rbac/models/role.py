"""
Role model for RBAC.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from ..base import RBACModel
from django.core.exceptions import ValidationError

class Role(RBACModel):
    """
    Role model for RBAC.
    """
    name = models.CharField(
        _('name'),
        max_length=255,
        unique=True,
        help_text=_('Name of the role.')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Description of the role.')
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        help_text=_('Parent role for inheritance.')
    )
    users = models.ManyToManyField(
        'users.User',
        through='rbac.UserRole',
        through_fields=('role', 'user'),
        related_name='assigned_roles',
        help_text=_('Users assigned to this role.')
    )

    class Meta:
        verbose_name = _('role')
        verbose_name_plural = _('roles')
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        """Validate the role."""
        if not self.name or self.name.strip() == '':
            raise ValidationError({'name': 'Role name cannot be empty.'})

    def get_all_permissions(self):
        """
        Get all permissions for this role, including inherited ones.
        """
        permissions = set(self.role_permissions.all())
        if self.parent:
            permissions.update(self.parent.get_all_permissions())
        return permissions

    def get_all_field_permissions(self):
        """
        Get all field permissions for this role, including inherited ones.
        """
        field_permissions = set(self.field_permissions.all())
        if self.parent:
            field_permissions.update(self.parent.get_all_field_permissions())
        return field_permissions 