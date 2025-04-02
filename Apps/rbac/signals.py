"""
Signal handlers for RBAC.
"""

from django.db.models.signals import post_migrate, post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.apps import apps
from django.core.cache import cache
from .base import RBACModel
from .models.role import Role
from .models.role_permission import RolePermission
from .models.user_role import UserRole
from .models.permission import RBACPermission, FieldPermission
from .permissions.cache_utils import _invalidate_user_permissions
from django.db.models import Q

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

@receiver(post_migrate)
def create_rbac_permissions(sender, **kwargs):
    """
    Signal handler to automatically create permissions for models inheriting from RBACModel.
    This runs after migrations to ensure all models are registered.
    """
    RBACPermission, FieldPermission = get_permission_models()
    
    # Get all models that inherit from RBACModel
    for model in apps.get_models():
        if issubclass(model, RBACModel):
            content_type = ContentType.objects.get_for_model(model)
            
            # Create model-level permissions
            for permission_type in ['view', 'add', 'change', 'delete']:
                permission_name = f'Can {permission_type} {model._meta.verbose_name}'
                RBACPermission.objects.get_or_create(
                    content_type=content_type,
                    codename=permission_type,
                    defaults={'name': permission_name}
                )
            
            # Create field-level permissions
            for field in model._meta.fields:
                # Skip private fields (starting with _)
                if field.name.startswith('_'):
                    continue
                
                # Create field permissions for each permission type
                for permission_type in ['view', 'add', 'change', 'delete']:
                    FieldPermission.objects.get_or_create(
                        content_type=content_type,
                        field_name=field.name,
                        permission_type=permission_type
                    )

@receiver([post_save, post_delete], sender=RolePermission)
def update_group_permissions(sender, instance, **kwargs):
    """Update permissions for all users with this role."""
    Role, RolePermission, UserRole = get_role_models()
    
    # Get all users with this role
    user_roles = UserRole.objects.filter(role=instance.role)
    users = [ur.user for ur in user_roles]
    
    # Invalidate permissions for each user
    for user in users:
        if instance.permission:
            _invalidate_user_permissions(user, instance.permission.content_type.model_class())
        if instance.field_permission:
            _invalidate_user_permissions(
                user,
                instance.field_permission.content_type.model_class()
            )

@receiver(post_save, sender=UserRole)
def update_user_groups(sender, instance, **kwargs):
    """Update user groups when user role changes."""
    if not instance.user:
        return

    # Get all roles for the user
    user_roles = UserRole.objects.filter(user=instance.user)
    role_ids = user_roles.values_list('role_id', flat=True)
    
    # Get all content types from role permissions
    content_types = ContentType.objects.filter(
        Q(rbacpermission__role_permissions__role_id__in=role_ids) |
        Q(field_permissions__role_permissions__role_id__in=role_ids)
    ).distinct()
    
    # Invalidate permissions for each content type
    for content_type in content_types:
        _invalidate_user_permissions(instance.user, content_type.model_class())

@receiver(post_save, sender=RBACPermission)
def invalidate_permission_cache(sender, instance, **kwargs):
    """
    Invalidate permission cache when a permission is saved.
    """
    user_ids = UserRole.objects.filter(
        role__role_permissions__permission=instance
    ).values_list('user_id', flat=True).distinct()

    model_class = instance.content_type.model_class()
    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
            _invalidate_user_permissions(user, model_class)
        except User.DoesNotExist:
            continue

@receiver(post_save, sender=FieldPermission)
def invalidate_field_permission_cache(sender, instance, **kwargs):
    """
    Invalidate field permission cache when a field permission is saved.
    """
    user_ids = UserRole.objects.filter(
        role__role_permissions__field_permission=instance
    ).values_list('user_id', flat=True).distinct()

    model_class = instance.content_type.model_class()
    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
            _invalidate_user_permissions(user, model_class)
        except User.DoesNotExist:
            continue

@receiver([post_save, post_delete], sender=UserRole)
def invalidate_user_role_cache_handler(sender, instance, **kwargs):
    """Invalidate cache when user roles change"""
    if not instance.user:
        return

    # Get all content types that have permissions
    content_types = ContentType.objects.filter(
        Q(rbacpermission__isnull=False) | Q(field_permissions__isnull=False)
    ).distinct()
    
    # Invalidate cache for each content type
    for content_type in content_types:
        _invalidate_user_permissions(instance.user, content_type.model_class())

@receiver(post_delete, sender=UserRole)
def invalidate_user_role_delete_cache(sender, instance, **kwargs):
    """
    Invalidate caches when a user role is deleted.
    """
    if not instance.user:
        return

    # Get all content types that have permissions
    content_types = ContentType.objects.filter(
        Q(rbacpermission__isnull=False) | Q(field_permissions__isnull=False)
    ).distinct()
    
    # Invalidate cache for each content type
    for content_type in content_types:
        _invalidate_user_permissions(instance.user, content_type.model_class())

@receiver(post_save, sender=Role)
def invalidate_role_cache(sender, instance, **kwargs):
    """
    Invalidate caches when a role is created or updated.
    """
    # Get all users with this role
    user_roles = UserRole.objects.filter(role=instance)
    users = [ur.user for ur in user_roles]
    
    # Get all content types that have permissions
    content_types = ContentType.objects.filter(
        Q(rbacpermission__isnull=False) | Q(field_permissions__isnull=False)
    ).distinct()
    
    # Invalidate cache for each user and content type
    for user in users:
        for content_type in content_types:
            _invalidate_user_permissions(user, content_type.model_class())

@receiver(post_delete, sender=Role)
def invalidate_role_delete_cache(sender, instance, **kwargs):
    """
    Invalidate caches when a role is deleted.
    """
    # Get all users with this role
    user_roles = UserRole.objects.filter(role=instance)
    users = [ur.user for ur in user_roles]
    
    # Get all content types that have permissions
    content_types = ContentType.objects.filter(
        Q(rbacpermission__isnull=False) | Q(field_permissions__isnull=False)
    ).distinct()
    
    # Invalidate cache for each user and content type
    for user in users:
        for content_type in content_types:
            _invalidate_user_permissions(user, content_type.model_class())

# Temporarily commented out to break circular dependency
# @receiver(m2m_changed, sender=User.roles.through)
# def handle_user_role_changes(sender, instance, action, **kwargs):
#     """
#     Handle changes to user roles through the M2M relationship.
#     """
#     if action in ["post_add", "post_remove", "post_clear"]:
#         invalidate_permissions(instance)
#         invalidate_field_permissions(instance) 