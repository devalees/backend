"""
Permission generation functions for RBAC.
"""

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from ..models import RBACPermission, FieldPermission

def generate_model_permissions(model_class):
    """Generate model-level permissions for a model."""
    content_type = ContentType.objects.get_for_model(model_class)
    model_name = model_class._meta.verbose_name

    # Define standard permissions
    permissions = [
        ('view', f'Can view {model_name}'),
        ('add', f'Can add {model_name}'),
        ('change', f'Can change {model_name}'),
        ('delete', f'Can delete {model_name}')
    ]

    # Create or update permissions
    created_permissions = []
    for codename, name in permissions:
        permission, created = RBACPermission.objects.get_or_create(
            content_type=content_type,
            codename=codename,
            defaults={'name': name}
        )
        if not created:
            permission.name = name
            permission.save()
        created_permissions.append(permission)
    
    return created_permissions

def generate_field_permissions(model_class):
    """Generate field-level permissions for a model."""
    content_type = ContentType.objects.get_for_model(model_class)
    
    # Get all fields from the model, excluding private fields and base model fields
    base_fields = {'id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'created_by_id', 'updated_by_id', 'is_active'}
    fields = [field.name for field in model_class._meta.fields 
             if not field.name.startswith('_') and field.name not in base_fields]
    
    # Define permission types
    permission_types = ['read', 'write', 'delete']
    
    # Create field permissions
    created_permissions = []
    for field_name in fields:
        for permission_type in permission_types:
            # Use get_or_create to avoid duplicates
            permission, created = FieldPermission.objects.get_or_create(
                content_type=content_type,
                field_name=field_name,
                permission_type=permission_type
            )
            created_permissions.append(permission)
    
    # Delete any field permissions that shouldn't exist
    FieldPermission.objects.filter(
        content_type=content_type
    ).exclude(
        field_name__in=fields,
        permission_type__in=permission_types
    ).delete()
    
    return created_permissions

def generate_permissions(model_class):
    """Generate all permissions for a model."""
    # Generate new permissions
    model_permissions = generate_model_permissions(model_class)
    field_permissions = generate_field_permissions(model_class)
    
    return model_permissions, field_permissions 