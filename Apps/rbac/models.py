from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from Core.models.base import TaskAwareModel

User = get_user_model()

class Role(TaskAwareModel):
    """
    Represents a role in the system that can be assigned to users.
    Roles are used to group permissions together.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_roles'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_roles'
    )

    class Meta:
        ordering = ['name']
        verbose_name = _('Role')
        verbose_name_plural = _('Roles')

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if not self.name:
            raise ValidationError({'name': 'Name is required.'})

class Permission(TaskAwareModel):
    """
    Model for storing permissions with task handling capabilities.
    """
    name = models.CharField(max_length=255)
    codename = models.CharField(max_length=100)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='rbac_permissions',
        default=1  # Default to User model's content type
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_permissions'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_permissions'
    )

    class Meta:
        unique_together = ['content_type', 'codename']
        ordering = ['codename']

    def __str__(self):
        return f"{self.name} ({self.codename})"

    def clean(self):
        super().clean()
        if not self.content_type:
            raise ValidationError({'content_type': 'Content type is required.'})
        if not self.codename:
            raise ValidationError({'codename': 'Codename is required.'})
        if not self.name:
            raise ValidationError({'name': 'Name is required.'})

class FieldPermission(TaskAwareModel):
    """
    Model for storing field-level permissions with task handling capabilities.
    """
    PERMISSION_TYPES = [
        ('view', 'View'),
        ('add', 'Add'),
        ('change', 'Change'),
        ('delete', 'Delete'),
    ]

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='field_permissions'
    )
    field_name = models.CharField(max_length=100)
    permission_type = models.CharField(max_length=10, choices=PERMISSION_TYPES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_field_permissions'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_field_permissions'
    )

    class Meta:
        unique_together = ['content_type', 'field_name', 'permission_type']
        ordering = ['field_name']

    def __str__(self):
        return f"{self.field_name} - {self.get_permission_type_display()}"

    def clean(self):
        super().clean()
        if not self.content_type:
            raise ValidationError({'content_type': 'Content type is required.'})
        if not self.field_name:
            raise ValidationError({'field_name': 'Field name is required.'})
        if not self.permission_type:
            raise ValidationError({'permission_type': 'Permission type is required.'})
        if self.permission_type not in dict(self.PERMISSION_TYPES):
            raise ValidationError({'permission_type': 'Invalid permission type.'})
        
        try:
            model = self.content_type.model_class()
            if not model:
                raise ValidationError({'content_type': 'Invalid content type: unable to get model class.'})
            if not hasattr(model, self.field_name):
                raise ValidationError({'field_name': f'Field {self.field_name} does not exist in model {model.__name__}.'})
        except (AttributeError, ContentType.DoesNotExist):
            raise ValidationError({'content_type': 'Invalid content type.'})

class RolePermission(models.Model):
    """
    Model for storing role-permission relationships.
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    field_permission = models.ForeignKey(FieldPermission, on_delete=models.CASCADE, null=True, blank=True, related_name='role_permissions')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_role_permissions')

    class Meta:
        unique_together = ['role', 'permission', 'field_permission']
        ordering = ['role', 'permission']

    def __str__(self):
        if self.field_permission:
            return f"{self.role.name} - {self.field_permission.permission_type}"
        return f"{self.role.name} - {self.permission.codename}"

    def clean(self):
        if not self.role:
            raise ValidationError({'role': 'Role is required.'})
        if not self.permission:
            raise ValidationError({'permission': 'Permission is required.'})
        if self.field_permission and self.field_permission.permission_type != self.permission.codename:
            raise ValidationError({'field_permission': 'Field permission type must match permission codename.'})

class UserRole(models.Model):
    """
    Model for storing user-role assignments.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_user_roles')

    class Meta:
        unique_together = ['user', 'role']
        ordering = ['user', 'role']

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

    def clean(self):
        if not self.user:
            raise ValidationError({'user': 'User is required.'})
        if not self.role:
            raise ValidationError({'role': 'Role is required.'})
        if UserRole.objects.filter(user=self.user, role=self.role).exists():
            raise ValidationError({'role': 'User already has this role.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
