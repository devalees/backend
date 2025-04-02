"""
RBAC models.
"""

from django.db import models
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings
from .base import RBACModel
from .permissions.utils import invalidate_permissions, invalidate_field_permissions
from django.contrib.auth import get_user_model

PERMISSION_TYPES = [
    ('view', 'View'),
    ('add', 'Add'),
    ('change', 'Change'),
    ('delete', 'Delete'),
]

class FieldPermission(RBACModel):
    """
    Model for field-level permissions.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=255)
    permission_type = models.CharField(max_length=50, choices=PERMISSION_TYPES)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('content_type', 'field_name', 'permission_type')
        ordering = ['content_type', 'field_name', 'permission_type']

    def __str__(self):
        return f"{self.permission_type} {self.field_name} ({self.content_type.model})"

    def clean(self):
        if not self.content_type_id:
            raise ValidationError(_('Content type is required.'))
        if not self.field_name:
            raise ValidationError(_('Field name is required.'))
        if not self.permission_type:
            raise ValidationError(_('Permission type is required.'))
        
        # Validate that the field exists on the model
        model = self.content_type.model_class()
        if not hasattr(model, self.field_name):
            raise ValidationError(_(f'Field {self.field_name} does not exist on model {model.__name__}'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Invalidate caches for all users with this field permission
        User = get_user_model()
        for user in User.objects.filter(user_roles__role__role_permissions__field_permission=self).distinct():
            invalidate_field_permissions(user, self.content_type.model, self.field_name)

class Role(RBACModel):
    """
    Role model that extends Django's Group model.
    """
    group = models.OneToOneField(Group, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(blank=True)
    name = models.CharField(max_length=150, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        if not self.name:
            raise ValidationError(_('Name is required.'))

    def save(self, *args, **kwargs):
        self.clean()
        if not self.group_id:
            # Create a new Group if one doesn't exist
            group = Group.objects.create(name=self.name)
            self.group = group
        else:
            # Update the group name if it changed
            if self.group.name != self.name:
                self.group.name = self.name
                self.group.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        group = self.group
        super().delete(*args, **kwargs)
        # Delete the associated Group
        if group:
            group.delete()

    @property
    def role_permissions(self):
        """Get all permissions associated with this role."""
        return RolePermission.objects.filter(role=self)

    @property
    def field_permissions(self):
        """Get all field permissions associated with this role."""
        return RolePermission.objects.filter(role=self, field_permission__isnull=False)

    @property
    def model_permissions(self):
        """Get all model-level permissions associated with this role."""
        return RolePermission.objects.filter(role=self, field_permission__isnull=True)

    @property
    def user_roles(self):
        """Get all user assignments for this role."""
        return UserRole.objects.filter(role=self)

class RolePermission(RBACModel):
    """
    Model that links roles to permissions.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, default=lambda: ContentType.objects.get_for_model(RBACPermission))
    object_id = models.PositiveIntegerField(default=1)
    permission = GenericForeignKey('content_type', 'object_id')
    field_permission = models.ForeignKey(FieldPermission, on_delete=models.CASCADE, null=True, blank=True, related_name='role_permissions')

    class Meta:
        unique_together = ('role', 'content_type', 'object_id', 'field_permission')
        ordering = ['role', 'content_type', 'object_id']

    def __str__(self):
        if self.field_permission:
            return f"{self.role} - {self.field_permission}"
        return f"{self.role} - {self.permission}"

    def clean(self):
        if not self.role:
            raise ValidationError(_('Role is required.'))
        if not self.content_type or not self.object_id:
            raise ValidationError('Content type and object ID are required.')
        if self.field_permission and self.field_permission.content_type != self.content_type:
            raise ValidationError('Field permission content type must match the permission content type.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Invalidate permissions cache for users with this role
        for user_role in self.role.user_roles.all():
            user_role.user.invalidate_permissions_cache()

class UserRole(RBACModel):
    """
    Model that links users to roles.
    """
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')

    class Meta:
        unique_together = ('user', 'role')
        ordering = ['user', 'role']

    def __str__(self):
        return f"{self.user} - {self.role}"

    def clean(self):
        if not self.user:
            raise ValidationError(_('User is required.'))
        if not self.role:
            raise ValidationError(_('Role is required.'))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        # Invalidate caches for this user
        invalidate_permissions(self.user, None)  # None means invalidate all models

class TestDocument(RBACModel):
    """Test model for RBAC permissions testing."""
    title = models.CharField(max_length=100)
    content = models.TextField()

    def __str__(self):
        return self.title 