"""
Utility functions for RBAC.
"""

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.apps import apps
from django.utils.translation import gettext_lazy as _

User = get_user_model()

def get_permission_models():
    """Get permission models to avoid circular imports."""
    RBACPermission = apps.get_model('rbac', 'RBACPermission')
    FieldPermission = apps.get_model('rbac', 'FieldPermission')
    return RBACPermission, FieldPermission

def get_role_models():
    """Get role models to avoid circular imports."""
    Role = apps.get_model('rbac', 'Role')
    RolePermission = apps.get_model('rbac', 'RolePermission')
    UserRole = apps.get_model('rbac', 'UserRole')
    return Role, RolePermission, UserRole

def get_user_roles(user):
    """Get all roles for a user."""
    if not user.is_authenticated:
        return []
    if user.is_superuser:
        return ['*']  # Superuser has all roles

    Role, RolePermission, UserRole = get_role_models()
    return list(UserRole.objects.filter(user=user).values_list('role__name', flat=True))

def get_role_permissions(role):
    """Get all permissions for a role."""
    Role, RolePermission, UserRole = get_role_models()
    RBACPermission, FieldPermission = get_permission_models()

    permissions = []
    role_permissions = RolePermission.objects.filter(role=role).select_related('permission', 'field_permission')

    for role_permission in role_permissions:
        if role_permission.permission:
            permissions.append(role_permission.permission.codename)
        if role_permission.field_permission:
            permissions.append(f'{role_permission.field_permission.field_name}_{role_permission.field_permission.permission_type}')

    return permissions

def get_role_field_permissions(role, model):
    """Get field-level permissions for a role on a model."""
    Role, RolePermission, UserRole = get_role_models()
    RBACPermission, FieldPermission = get_permission_models()

    try:
        content_type = ContentType.objects.get_for_model(model)
    except ContentType.DoesNotExist:
        return {}

    field_permissions = {}
    role_permissions = RolePermission.objects.filter(
        role=role,
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

def get_user_permissions(user, model=None):
    """Get all permissions for a user."""
    if not user.is_authenticated:
        return set()
    if user.is_superuser:
        return set('*')  # Superuser has all permissions

    Role, RolePermission, UserRole = get_role_models()
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
            if model is None or role_permission.permission.content_type.model_class() == model:
                permissions.add(role_permission.permission.codename)
        if role_permission.field_permission:
            if model is None or role_permission.field_permission.content_type.model_class() == model:
                permissions.add(f'{role_permission.field_permission.field_name}_{role_permission.field_permission.permission_type}')

    return permissions

def get_user_field_permissions(user, model):
    """Get field-level permissions for a user on a model."""
    if not user.is_authenticated:
        return {}
    if user.is_superuser:
        return {'*': {'*'}}  # Superuser has all permissions

    Role, RolePermission, UserRole = get_role_models()
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

def has_permission(user, permission_codename, obj=None):
    """Check if user has a specific permission."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    Role, RolePermission, UserRole = get_role_models()
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

    Role, RolePermission, UserRole = get_role_models()
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