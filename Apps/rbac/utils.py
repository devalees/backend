from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType
from .models import Role, Permission, UserRole, FieldPermission

User = get_user_model()

def has_permission(user, permission_codename, model=None, field=None):
    """
    Check if a user has a specific permission through their roles.
    Optionally check for field-level permissions.
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_staff:
        return True
        
    if model and field:
        # Check for field-level permission
        content_type = ContentType.objects.get_for_model(model)
        return UserRole.objects.filter(
            user=user,
            role__role_permissions__field_permission__content_type=content_type,
            role__role_permissions__field_permission__field_name=field,
            role__role_permissions__permission__codename=permission_codename
        ).exists()
    
    # Check for model-level permission
    return UserRole.objects.filter(
        user=user,
        role__role_permissions__permission__codename=permission_codename,
        role__role_permissions__field_permission__isnull=True
    ).exists()

def has_role(user, role_name):
    """
    Check if a user has a specific role.
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_staff:
        return True
        
    return UserRole.objects.filter(
        user=user,
        role__name=role_name
    ).exists()

def get_user_permissions(user, model=None):
    """
    Get all permissions for a user through their roles.
    Optionally filter by model for field-level permissions.
    """
    if not user or not user.is_authenticated:
        return set()
    
    if user.is_staff:
        if model:
            content_type = ContentType.objects.get_for_model(model)
            return set(FieldPermission.objects.filter(
                content_type=content_type
            ).values_list('permission_type', flat=True))
        return set(Permission.objects.values_list('codename', flat=True))
    
    if model:
        content_type = ContentType.objects.get_for_model(model)
        return set(FieldPermission.objects.filter(
            role_permissions__role__user_roles__user=user,
            content_type=content_type
        ).values_list('permission_type', flat=True))
        
    return set(Permission.objects.filter(
        role_permissions__role__user_roles__user=user,
        role_permissions__field_permission__isnull=True
    ).values_list('codename', flat=True))

def get_user_roles(user):
    """
    Get all roles for a user.
    """
    if not user or not user.is_authenticated:
        return []
    
    if user.is_staff:
        return list(Role.objects.values_list('name', flat=True))
        
    return list(Role.objects.filter(
        user_roles__user=user
    ).values_list('name', flat=True))

def get_field_permissions(user, model):
    """
    Get field-level permissions for a user on a specific model.
    """
    if not user or not user.is_authenticated:
        return {}
    
    if user.is_staff:
        content_type = ContentType.objects.get_for_model(model)
        return {
            fp.field_name: fp.permission_type
            for fp in FieldPermission.objects.filter(content_type=content_type)
        }
    
    content_type = ContentType.objects.get_for_model(model)
    return {
        fp.field_name: fp.permission_type
        for fp in FieldPermission.objects.filter(
            role_permissions__role__user_roles__user=user,
            content_type=content_type
        ).distinct()
    }

def require_permission(permission_codename, model=None, field=None):
    """
    Decorator to require a specific permission.
    Optionally check for field-level permissions.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not has_permission(request.user, permission_codename, model, field):
                raise PermissionDenied(
                    f"You don't have permission to perform this action. "
                    f"Required permission: {permission_codename}"
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def require_role(role_name):
    """
    Decorator to require a specific role.
    """
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not has_role(request.user, role_name):
                raise PermissionDenied(
                    f"You don't have the required role to perform this action. "
                    f"Required role: {role_name}"
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator 