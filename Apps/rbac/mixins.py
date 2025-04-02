"""
RBAC mixins for Django models and views.
"""

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db import models
from django.utils.translation import gettext_lazy as _
from .models import RolePermission, UserRole

class RBACModelMixin:
    """
    Mixin to add RBAC functionality to any model.
    """
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name=_('Created by')
    )
    updated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name=_('Updated by')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_view(self, user: User) -> bool:
        """Check if user can view this object."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return self.check_permission(user, 'view')

    def can_add(self, user: User) -> bool:
        """Check if user can add this type of object."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return self.check_permission(user, 'add')

    def can_change(self, user: User) -> bool:
        """Check if user can change this object."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return self.check_permission(user, 'change')

    def can_delete(self, user: User) -> bool:
        """Check if user can delete this object."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return self.check_permission(user, 'delete')

    def check_permission(self, user: User, action: str) -> bool:
        """Check if user has permission for given action."""
        content_type = ContentType.objects.get_for_model(self)
        
        # Get user's roles
        user_roles = UserRole.objects.filter(user=user)
        
        # Check model-level permissions first
        model_permissions = RolePermission.objects.filter(
            role__in=user_roles.values_list('role', flat=True),
            content_type=content_type,
            object_id__isnull=True
        )
        
        if model_permissions.exists():
            return any(getattr(perm, f'can_{action}') for perm in model_permissions)
        
        # Check object-level permissions
        object_permissions = RolePermission.objects.filter(
            role__in=user_roles.values_list('role', flat=True),
            content_type=content_type,
            object_id=self.pk
        )
        
        return any(getattr(perm, f'can_{action}') for perm in object_permissions)

    def get_accessible_fields(self, user: User) -> list:
        """Get list of fields accessible to user."""
        if not user.is_authenticated:
            return []
        if user.is_superuser:
            return [field.name for field in self._meta.fields]
        
        accessible_fields = []
        for field in self._meta.fields:
            if field.name in ['created_by', 'updated_by', 'created_at', 'updated_at']:
                accessible_fields.append(field.name)
            elif self.can_view(user):
                accessible_fields.append(field.name)
        
        return accessible_fields

    @classmethod
    def get_queryset_for_user(cls, user: User):
        """Get queryset of objects user can access."""
        if not user.is_authenticated:
            return cls.objects.none()
        if user.is_superuser:
            return cls.objects.all()
        
        content_type = ContentType.objects.get_for_model(cls)
        user_roles = UserRole.objects.filter(user=user)
        
        # Get model-level permissions
        model_permissions = RolePermission.objects.filter(
            role__in=user_roles.values_list('role', flat=True),
            content_type=content_type,
            object_id__isnull=True,
            can_view=True
        )
        
        if model_permissions.exists():
            return cls.objects.all()
        
        # Get object-level permissions
        object_permissions = RolePermission.objects.filter(
            role__in=user_roles.values_list('role', flat=True),
            content_type=content_type,
            can_view=True
        )
        
        return cls.objects.filter(pk__in=object_permissions.values_list('object_id', flat=True))

    def save(self, *args, **kwargs):
        """Set created_by and updated_by fields."""
        if not self.pk:  # New object
            self.created_by = kwargs.pop('user', None)
        self.updated_by = kwargs.pop('user', None)
        super().save(*args, **kwargs)

class RBACPermissionRequiredMixin:
    """
    Mixin to check RBAC permissions in views.
    """
    permission_required = None  # 'view', 'add', 'change', or 'delete'

    def test_func(self):
        """Check if user has required permission."""
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True
        
        if hasattr(self, 'get_object'):
            obj = self.get_object()
            return getattr(obj, f'can_{self.permission_required}')(self.request.user)
        else:
            model = self.queryset.model
            content_type = ContentType.objects.get_for_model(model)
            user_roles = UserRole.objects.filter(user=self.request.user)
            
            # Check model-level permissions
            model_permissions = RolePermission.objects.filter(
                role__in=user_roles.values_list('role', flat=True),
                content_type=content_type,
                object_id__isnull=True
            )
            
            if model_permissions.exists():
                return any(getattr(perm, f'can_{self.permission_required}') for perm in model_permissions)
            
            return False

    def handle_no_permission(self):
        """Handle permission denied."""
        raise PermissionDenied(_('You do not have permission to perform this action.')) 