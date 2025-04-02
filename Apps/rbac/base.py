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
        if user:
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

    def _get_user_roles(self, user):
        """Get all active roles for a user."""
        if not user.is_authenticated:
            return []
        from .models import UserRole
        return UserRole.objects.filter(
            user=user,
            is_active=True
        ).select_related('role').values_list('role', flat=True)

    def _has_permission(self, user, permission_codename):
        """Check if user has a specific permission through their roles."""
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        if hasattr(self, 'user') and self.user == user:
            return True

        content_type = ContentType.objects.get_for_model(self)
        from .models import RBACPermission, RolePermission
        try:
            permission = RBACPermission.objects.get(
                codename=permission_codename,
                content_type=content_type
            )
            has_permission = RolePermission.objects.filter(
                role__in=self._get_user_roles(user),
                permission=permission,
                is_active=True
            ).exists()
            return has_permission
        except RBACPermission.DoesNotExist:
            return False

    def can_view(self, user):
        """Check if user can view this object."""
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return self._has_permission(user, f'view_{self._meta.model_name}')

    def can_add(self, user):
        """Check if user can add objects of this type."""
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return self._has_permission(user, f'add_{self._meta.model_name}')

    def can_change(self, user):
        """Check if user can change this object."""
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return self._has_permission(user, f'change_{self._meta.model_name}')

    def can_delete(self, user):
        """Check if user can delete this object."""
        if not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return self._has_permission(user, f'delete_{self._meta.model_name}')

    def check_permission(self, user, action):
        """Check if user has permission for the given action."""
        if not user.is_authenticated:
            raise PermissionDenied("User is not authenticated.")
        if user.is_superuser or user.is_staff:
            return True

        has_permission = False
        if action == 'view':
            has_permission = self.can_view(user)
        elif action == 'add':
            has_permission = self.can_add(user)
        elif action == 'change':
            has_permission = self.can_change(user)
        elif action == 'delete':
            has_permission = self.can_delete(user)

        if not has_permission:
            raise PermissionDenied(f"User does not have {action} permission.")
        return True

    def get_accessible_fields(self, user):
        """Get fields that the user can access."""
        if not user.is_authenticated:
            return {}
        if user.is_superuser or user.is_staff:
            return {field.name: {'view', 'add', 'change'} for field in self._meta.fields}

        content_type = ContentType.objects.get_for_model(self)
        accessible_fields = {}

        # Get field permissions for user's roles
        from .models import RolePermission, FieldPermission
        role_permissions = RolePermission.objects.filter(
            role__in=self._get_user_roles(user),
            field_permission__content_type=content_type,
            is_active=True
        ).select_related('field_permission')

        for role_perm in role_permissions:
            if not role_perm.field_permission:
                continue
            field_name = role_perm.field_permission.field_name
            if field_name not in accessible_fields:
                accessible_fields[field_name] = set()
            accessible_fields[field_name].add(role_perm.field_permission.permission_type)

        return accessible_fields

    @classmethod
    def get_queryset_for_user(cls, user, queryset=None):
        """Get queryset filtered by user's permissions."""
        if not user.is_authenticated:
            return cls.objects.none()
        if user.is_superuser or user.is_staff:
            return queryset or cls.objects.all()

        if queryset is None:
            queryset = cls.objects.all()

        # Include objects owned by the user
        user_objects = queryset.filter(user=user)

        # Include objects accessible through roles
        content_type = ContentType.objects.get_for_model(cls)
        from .models import RBACPermission, RolePermission, UserRole
        try:
            view_permission = RBACPermission.objects.get(
                codename=f'view_{cls._meta.model_name}',
                content_type=content_type
            )
            # Check if user has view permission through any of their roles
            has_view_permission = RolePermission.objects.filter(
                role__in=UserRole.objects.filter(
                    user=user,
                    is_active=True
                ).values_list('role', flat=True),
                permission=view_permission,
                is_active=True
            ).exists()
            
            if has_view_permission:
                return queryset
            return user_objects
        except RBACPermission.DoesNotExist:
            return user_objects

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