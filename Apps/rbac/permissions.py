"""
Permission functions for RBAC.
"""

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.apps import apps
from django.core.cache import cache
from functools import wraps
from rest_framework import permissions
from .permissions.cache_utils import _get_cache_key
from .permissions.caching import (
    get_user_permissions,
    get_user_field_permissions,
    invalidate_permission_caches,
)
from .models import RBACPermission, FieldPermission, RolePermission, UserRole

User = get_user_model()

def get_permission_models():
    """Get permission models to avoid circular imports."""
    RBACPermission = apps.get_model('rbac', 'RBACPermission')
    FieldPermission = apps.get_model('rbac', 'FieldPermission')
    return RBACPermission, FieldPermission

def get_role_models():
    """Get role models to avoid circular imports."""
    UserRole = apps.get_model('rbac', 'UserRole')
    RolePermission = apps.get_model('rbac', 'RolePermission')
    return UserRole, RolePermission

def get_user_role_model():
    """Get the UserRole model using lazy import."""
    return apps.get_model('rbac', 'UserRole')

def _get_cache_key(user_id, model, permission_type=None, field_name=None):
    """Generate a cache key for permission checks"""
    content_type = ContentType.objects.get_for_model(model)
    if field_name:
        return f'rbac:field_permission:{user_id}:{content_type.id}:{field_name}'
    elif permission_type:
        return f'rbac:permission:{user_id}:{content_type.id}:{permission_type}'
    else:
        return f'rbac:permissions:{user_id}:{content_type.id}'

def _invalidate_user_permissions(user_id, model):
    """Invalidate all permission caches for a user and model"""
    content_type = ContentType.objects.get_for_model(model)
    cache_keys = [
        f'rbac:permissions:{user_id}:{content_type.id}',
        f'rbac:field_permissions:{user_id}:{content_type.id}'
    ]
    cache.delete_many(cache_keys)

def has_permission(user, permission_codename, obj=None):
    """Check if user has a specific permission."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    UserRole, RolePermission = get_role_models()
    RBACPermission, FieldPermission = get_permission_models()

    # Get user's roles
    user_roles = UserRole.objects.filter(user=user).select_related('role')
    if not user_roles.exists():
        return False

    # Get permission
    try:
        permission = RBACPermission.objects.get(codename=permission_codename)
    except RBACPermission.DoesNotExist:
        return False

    # Check if any of user's roles have this permission
    return RolePermission.objects.filter(
        role__in=[ur.role for ur in user_roles],
        permission=permission
    ).exists()

def has_field_permission(user, model, field_name, permission_type, obj=None):
    """Check if user has permission for a specific field."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    UserRole, RolePermission = get_role_models()
    RBACPermission, FieldPermission = get_permission_models()

    # Get user's roles
    user_roles = UserRole.objects.filter(user=user).select_related('role')
    if not user_roles.exists():
        return False

    # Get content type
    try:
        content_type = ContentType.objects.get_for_model(model)
    except ContentType.DoesNotExist:
        return False

    # Get field permission
    try:
        field_permission = FieldPermission.objects.get(
            content_type=content_type,
            field_name=field_name,
            permission_type=permission_type
        )
    except FieldPermission.DoesNotExist:
        return False

    # Check if any of user's roles have this field permission
    return RolePermission.objects.filter(
        role__in=[ur.role for ur in user_roles],
        field_permission=field_permission
    ).exists()

def get_user_permissions(user, obj=None):
    """Get all permissions for a user."""
    if not user.is_authenticated:
        return set()
    if user.is_superuser:
        return set('*')  # Superuser has all permissions

    UserRole, RolePermission = get_role_models()
    RBACPermission, FieldPermission = get_permission_models()

    # Get user's roles
    user_roles = UserRole.objects.filter(user=user).select_related('role')
    if not user_roles.exists():
        return set()

    # Get all permissions from user's roles
    permissions = set()
    role_permissions = RolePermission.objects.filter(
        role__in=[ur.role for ur in user_roles]
    ).select_related('permission', 'field_permission')

    for role_permission in role_permissions:
        if role_permission.permission:
            permissions.add(role_permission.permission.codename)
        if role_permission.field_permission:
            permissions.add(f'{role_permission.field_permission.field_name}_{role_permission.field_permission.permission_type}')

    return permissions

def get_field_permissions(user, model, obj=None):
    """Get all field permissions for a user on a model."""
    if not user.is_authenticated:
        return {}
    if user.is_superuser:
        return {'*': {'*'}}  # Superuser has all permissions

    UserRole, RolePermission = get_role_models()
    RBACPermission, FieldPermission = get_permission_models()

    # Get user's roles
    user_roles = UserRole.objects.filter(user=user).select_related('role')
    if not user_roles.exists():
        return {}

    # Get content type
    try:
        content_type = ContentType.objects.get_for_model(model)
    except ContentType.DoesNotExist:
        return {}

    # Get all field permissions from user's roles
    field_permissions = {}
    role_permissions = RolePermission.objects.filter(
        role__in=[ur.role for ur in user_roles],
        field_permission__content_type=content_type
    ).select_related('field_permission')

    for role_permission in role_permissions:
        if role_permission.field_permission:
            field_name = role_permission.field_permission.field_name
            permission_type = role_permission.field_permission.permission_type
            if field_name not in field_permissions:
                field_permissions[field_name] = set()
            field_permissions[field_name].add(permission_type)

    return field_permissions

def require_permission(permission_codename):
    """Decorator to require a specific permission."""
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not has_permission(request.user, permission_codename):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def require_field_permission(model, field_name, permission_type):
    """Decorator to require a specific field permission."""
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not has_field_permission(request.user, model, field_name, permission_type):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def require_role(role_name):
    """
    Decorator to require a specific role for a view.
    Results are cached to improve performance.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not has_role(request.user, role_name):
                raise PermissionDenied(f"You don't have the required role: {role_name}")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def has_role(user, role_name):
    """
    Check if a user has a specific role.
    Results are cached to improve performance.
    """
    if not user.is_authenticated:
        return False

    cache_key = f'rbac:role:{user.id}:{role_name}'
    cached_result = cache.get(cache_key)
    
    if cached_result is not None:
        return cached_result

    from .models import UserRole
    has_role = UserRole.objects.filter(
        user=user,
        role__name=role_name
    ).exists()

    # Cache the result
    cache.set(cache_key, has_role, timeout=300)  # Cache for 5 minutes
    return has_role

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admin users.
        return request.user and request.user.is_staff

class CanManageRoles(permissions.BasePermission):
    """
    Custom permission to only allow users with role management permissions.
    """
    def has_permission(self, request, view):
        # Admin users can always manage roles
        if request.user and request.user.is_staff:
            return True

        # For non-admin users, check if they have the required permission
        if request.method in permissions.SAFE_METHODS:
            return has_permission(request.user, 'view_role', request.queryset.model)
        else:
            return has_permission(request.user, 'change_role', request.queryset.model)

    def has_object_permission(self, request, view, obj):
        # Admin users can always manage roles
        if request.user and request.user.is_staff:
            return True

        # For non-admin users, check if they have the required permission
        if request.method in permissions.SAFE_METHODS:
            return has_permission(request.user, 'view_role', obj)
        else:
            return has_permission(request.user, 'change_role', obj)

def has_permission(user, permission):
    """
    Check if a user has a specific permission.
    
    Args:
        user: The user to check permissions for
        permission: The permission to check (codename)
        
    Returns:
        bool: True if the user has the permission, False otherwise
    """
    if not user or not permission:
        return False
        
    # Get cached permissions
    permissions = get_user_permissions(user)
    
    # Check if permission exists in cache
    return permission in permissions

def has_field_permission(user, content_type, field_name, permission_type):
    """
    Check if a user has a specific field permission.
    
    Args:
        user: The user to check permissions for
        content_type: The content type to check permissions for
        field_name: The field name to check permissions for
        permission_type: The type of permission to check (read/write)
        
    Returns:
        bool: True if the user has the field permission, False otherwise
    """
    if not user or not content_type or not field_name or not permission_type:
        return False
        
    # Get cached field permissions
    field_permissions = get_user_field_permissions(user)
    
    # Check if field permission exists in cache
    key = (content_type.id, field_name, permission_type)
    return key in field_permissions

def get_user_roles(user):
    """
    Get all roles for a user.
    
    Args:
        user: The user to get roles for
        
    Returns:
        QuerySet: QuerySet of Role objects
    """
    if not user:
        return []
        
    UserRole = get_user_role_model()
    return UserRole.objects.filter(user=user).select_related('role')

def get_cached_user_permissions(user, model):
    """
    Get cached permissions for a user on a specific model.
    """
    cache_key = f'user_permissions_{user.id}_{model._meta.model_name}'
    permissions = cache.get(cache_key)
    
    if permissions is None:
        # Get all permissions through user's roles
        permissions = set()
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        
        for user_role in user_roles:
            role_permissions = RolePermission.objects.filter(
                role=user_role.role,
                content_type=ContentType.objects.get_for_model(model)
            )
            
            for role_permission in role_permissions:
                if role_permission.field_permission:
                    permissions.add(role_permission.field_permission.permission_type)
                else:
                    permissions.add(role_permission.permission.codename)
        
        # Cache the permissions
        cache.set(cache_key, permissions, timeout=300)  # Cache for 5 minutes
    
    return permissions

def get_cached_field_permissions(user, model, field_name=None):
    """
    Get cached field permissions for a user on a specific model and field.
    """
    cache_key = f'field_permissions_{user.id}_{model._meta.model_name}'
    if field_name:
        cache_key += f'_{field_name}'
    
    field_permissions = cache.get(cache_key)
    
    if field_permissions is None:
        field_permissions = {}
        user_roles = UserRole.objects.filter(user=user, is_active=True)
        content_type = ContentType.objects.get_for_model(model)
        
        for user_role in user_roles:
            role_permissions = RolePermission.objects.filter(
                role=user_role.role,
                content_type=content_type,
                field_permission__isnull=False
            )
            
            for role_permission in role_permissions:
                field_name = role_permission.field_permission.field_name
                if field_name not in field_permissions:
                    field_permissions[field_name] = set()
                field_permissions[field_name].add(role_permission.field_permission.permission_type)
        
        # Cache the field permissions
        cache.set(cache_key, field_permissions, timeout=300)  # Cache for 5 minutes
    
    if field_name:
        return field_permissions.get(field_name, set())
    return field_permissions

def has_permission(permission_codename):
    """
    Decorator to check if a user has a specific permission.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("User must be authenticated.")
            
            model = kwargs.get('model', None)
            if not model:
                raise ValueError("Model must be specified in kwargs.")
            
            permissions = get_cached_user_permissions(request.user, model)
            if permission_codename not in permissions:
                raise PermissionDenied(f"User does not have permission: {permission_codename}")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def has_field_permission(permission_type):
    """
    Decorator to check if a user has permission on a specific field.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("User must be authenticated.")
            
            model = kwargs.get('model', None)
            field_name = kwargs.get('field_name', None)
            
            if not model or not field_name:
                raise ValueError("Model and field_name must be specified in kwargs.")
            
            field_permissions = get_cached_field_permissions(request.user, model, field_name)
            if permission_type not in field_permissions:
                raise PermissionDenied(f"User does not have {permission_type} permission on field: {field_name}")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

class RBACPermissionMixin:
    """
    Mixin to add RBAC permission checking to views.
    """
    def has_permission(self, user, permission_codename):
        """
        Check if user has a specific permission.
        """
        if not user.is_authenticated:
            return False
        
        model = getattr(self, 'model', None)
        if not model:
            return False
        
        permissions = get_cached_user_permissions(user, model)
        return permission_codename in permissions
    
    def has_field_permission(self, user, field_name, permission_type):
        """
        Check if user has permission on a specific field.
        """
        if not user.is_authenticated:
            return False
        
        model = getattr(self, 'model', None)
        if not model:
            return False
        
        field_permissions = get_cached_field_permissions(user, model, field_name)
        return permission_type in field_permissions 