from rest_framework import serializers
from .models import UserRole, Role, Permission
from Apps.users.models import User
from django.db import models
from django.contrib.auth import get_user_model
from Apps.entity.models import Organization

class JsonApiRelatedField(serializers.PrimaryKeyRelatedField):
    """Custom field for JSON:API relationships"""
    def __init__(self, **kwargs):
        self.resource_name = kwargs.pop('resource_name', None)
        super().__init__(**kwargs)

class JsonApiSerializerMixin:
    """Mixin to format data according to JSON:API specification"""
    def to_representation(self, instance):
        """Convert the resource object into a JSON:API formatted dict"""
        representation = super().to_representation(instance)
        
        # Extract fields that should be at root level
        root_fields = {
            'id': str(instance.pk),
            'type': self.Meta.resource_name,
            'name': representation.pop('name', None)
        }
        
        # Remove None values from root_fields
        root_fields = {k: v for k, v in root_fields.items() if v is not None}
        
        # Move remaining fields to attributes
        data = {
            **root_fields,
            'attributes': representation,
            'relationships': self.get_relationships(instance)
        }
        return data
    
    def get_relationships(self, instance):
        """Get relationships for the resource object"""
        relationships = {}
        
        # Ensure permissions relationship is always included for roles
        if hasattr(self.Meta, 'resource_name') and self.Meta.resource_name == 'roles':
            relationships['permissions'] = {'data': []}
            if hasattr(instance, 'permissions'):
                relationships['permissions']['data'] = [
                    {'type': 'permissions', 'id': str(perm.id)}
                    for perm in instance.permissions.all()
                ]
        
        # Add other relationships
        for field_name, field in self.fields.items():
            if isinstance(field, serializers.RelatedField):
                relationships[field_name] = {
                    'data': None
                }
                
                # Get the related instance
                related = getattr(instance, field_name, None)
                if related:
                    if isinstance(field, serializers.ManyRelatedField):
                        # For many-to-many relationships
                        relationships[field_name]['data'] = [
                            {
                                'type': self._get_resource_type(field.child_relation),
                                'id': str(item.id)
                            }
                            for item in related.all()
                        ]
                    else:
                        # For foreign key relationships
                        relationships[field_name]['data'] = {
                            'type': self._get_resource_type(field),
                            'id': str(related.id)
                        }
        
        return relationships

    def _get_resource_type(self, field):
        """Get the resource type for a field"""
        # Try to get resource_name from field
        if hasattr(field, 'resource_name'):
            return field.resource_name
        
        # For PrimaryKeyRelatedField, try to get model name
        if isinstance(field, serializers.PrimaryKeyRelatedField) and field.queryset is not None:
            model = field.queryset.model
            return model._meta.model_name.lower()
            
        # For other fields, try to get parent serializer's resource name
        if hasattr(self.Meta, 'resource_name'):
            return self.Meta.resource_name
            
        # Fallback to a generic name
        return 'resource'

class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model"""
    user = JsonApiRelatedField(queryset=User.objects.all(), resource_name='users')
    role = JsonApiRelatedField(queryset=Role.objects.all(), resource_name='roles')
    assigned_by = JsonApiRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
        resource_name='users'
    )
    delegated_by = JsonApiRelatedField(
        queryset=UserRole.objects.all(),
        required=False,
        allow_null=True,
        resource_name='user_roles'
    )

    class Meta:
        model = UserRole
        fields = [
            'id', 'user', 'role', 'organization', 'assigned_by',
            'delegated_by', 'is_active', 'is_delegated', 'deactivated_at',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'deactivated_at']

    def validate(self, data):
        """Validate the user role assignment"""
        # Ensure user and role belong to the same organization
        if data['user'].organization != data['organization']:
            raise serializers.ValidationError(
                "User must belong to the same organization"
            )
        if data['role'].organization != data['organization']:
            raise serializers.ValidationError(
                "Role must belong to the same organization"
            )

        # Validate delegation
        if data.get('delegated_by') and data['delegated_by'].organization != data['organization']:
            raise serializers.ValidationError(
                "Delegating role must belong to the same organization"
            )

        # Validate assigned_by
        if data.get('assigned_by') and data['assigned_by'].organization != data['organization']:
            raise serializers.ValidationError(
                "Assigning user must belong to the same organization"
            )

        return data

    def create(self, validated_data):
        """Create a new user role assignment"""
        # Set assigned_by to the current user if not provided
        if not validated_data.get('assigned_by'):
            validated_data['assigned_by'] = self.context['request'].user

        return super().create(validated_data)

class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating UserRole model"""
    class Meta:
        model = UserRole
        fields = ['is_active', 'notes']
        read_only_fields = ['user', 'role', 'organization', 'assigned_by', 'delegated_by']

    def update(self, instance, validated_data):
        """Update user role assignment"""
        if 'is_active' in validated_data:
            if validated_data['is_active']:
                instance.activate()
            else:
                instance.deactivate()
            validated_data.pop('is_active')

        return super().update(instance, validated_data)

class RoleSerializer(JsonApiSerializerMixin, serializers.ModelSerializer):
    """Serializer for Role model"""
    permissions = JsonApiRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        resource_name='permissions',
        required=False
    )
    parent = JsonApiRelatedField(
        queryset=Role.objects.all(),
        required=False,
        allow_null=True,
        resource_name='roles'
    )
    organization = JsonApiRelatedField(
        queryset=Organization.objects.all(),
        resource_name='organizations'
    )

    class Meta:
        model = Role
        resource_name = 'roles'
        fields = [
            'id', 'name', 'description', 'organization', 'parent',
            'is_active', 'permissions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_name(self, value):
        """Validate role name"""
        if not value or not isinstance(value, str):
            raise serializers.ValidationError("Name must be a non-empty string")
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters long")
        if len(value) > 100:
            raise serializers.ValidationError("Name must not exceed 100 characters")
        return value

    def validate_description(self, value):
        """Validate role description"""
        if value and not isinstance(value, str):
            raise serializers.ValidationError("Description must be a string")
        if value and len(value) > 500:
            raise serializers.ValidationError("Description must not exceed 500 characters")
        return value

    def validate_organization(self, value):
        """Validate organization"""
        if not value:
            raise serializers.ValidationError("Organization is required")
        if not value.is_active:
            raise serializers.ValidationError("Organization must be active")
        return value

    def validate_permissions(self, value):
        """Validate that all permissions belong to the same organization"""
        organization = self.context.get('organization') or (self.instance.organization if self.instance else None)
        if organization:
            for permission in value:
                if permission.organization != organization:
                    raise serializers.ValidationError(
                        f"Permission {permission.name} does not belong to the same organization"
                    )
        return value

    def validate(self, data):
        """Validate role data"""
        # Ensure parent role belongs to the same organization
        if data.get('parent') and data['parent'].organization != data['organization']:
            raise serializers.ValidationError(
                "Parent role must belong to the same organization"
            )

        # Check for duplicate role names within the same organization
        if Role.objects.filter(
            name=data['name'],
            organization=data['organization']
        ).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError(
                "A role with this name already exists in the organization"
            )

        return data

    def get_relationships(self, instance):
        """Get relationships for the resource object"""
        relationships = super().get_relationships(instance)
        # Ensure permissions relationship is always included
        if 'permissions' not in relationships:
            relationships['permissions'] = {'data': []}
        return relationships

class PermissionSerializer(JsonApiSerializerMixin, serializers.ModelSerializer):
    """Serializer for Permission model"""
    class Meta:
        model = Permission
        resource_name = 'permissions'
        fields = [
            'id', 'name', 'description', 'code', 'organization',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_name(self, value):
        """Validate permission name"""
        if not value or not isinstance(value, str):
            raise serializers.ValidationError("Name must be a non-empty string")
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters long")
        if len(value) > 100:
            raise serializers.ValidationError("Name must not exceed 100 characters")
        return value

    def validate_description(self, value):
        """Validate permission description"""
        if value and not isinstance(value, str):
            raise serializers.ValidationError("Description must be a string")
        if value and len(value) > 500:
            raise serializers.ValidationError("Description must not exceed 500 characters")
        return value

    def validate_organization(self, value):
        """Validate organization"""
        if not value:
            raise serializers.ValidationError("Organization is required")
        if not value.is_active:
            raise serializers.ValidationError("Organization must be active")
        return value

    def validate_code(self, value):
        """Validate permission code format"""
        if not value or not isinstance(value, str):
            raise serializers.ValidationError("Code must be a non-empty string")
        if not value.replace('.', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Code can only contain alphanumeric characters, dots, and underscores"
            )
        if len(value) < 3:
            raise serializers.ValidationError("Code must be at least 3 characters long")
        if len(value) > 100:
            raise serializers.ValidationError("Code must not exceed 100 characters")
        return value

    def validate(self, data):
        """Validate permission data"""
        # Check for duplicate permission codes within the same organization
        if Permission.objects.filter(
            code=data['code'],
            organization=data['organization']
        ).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError(
                "A permission with this code already exists in the organization"
            )

        # Check for duplicate permission names within the same organization
        if Permission.objects.filter(
            name=data['name'],
            organization=data['organization']
        ).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError(
                "A permission with this name already exists in the organization"
            )

        return data 