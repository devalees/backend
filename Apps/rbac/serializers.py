"""
Serializers for RBAC.
"""

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework import serializers
from .models import (
    Role, RolePermission, UserRole,
    RBACPermission, FieldPermission
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = ('id',)

    def to_representation(self, instance):
        """Convert user instance to primitive types."""
        if self.context.get('return_id_only'):
            return instance.id
        return super().to_representation(instance)

class RBACPermissionSerializer(serializers.ModelSerializer):
    """Serializer for RBACPermission model."""
    content_type = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all())
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RBACPermission
        fields = ('id', 'content_type', 'codename', 'name', 'created_by', 'updated_by')
        read_only_fields = ('created_by', 'updated_by')

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['updated_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data

class FieldPermissionSerializer(serializers.ModelSerializer):
    """Serializer for FieldPermission model."""
    content_type = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all(), write_only=True)
    content_type_info = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = FieldPermission
        fields = ('id', 'content_type', 'content_type_info', 'field_name', 'permission_type', 'created_by', 'updated_by')
        read_only_fields = ('created_by', 'updated_by', 'content_type_info')

    def get_content_type_info(self, obj):
        return {
            'id': obj.content_type.id,
            'app_label': obj.content_type.app_label,
            'model': obj.content_type.model
        }

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['updated_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['content_type'] = self.get_content_type_info(instance)
        return data

class RolePermissionSerializer(serializers.ModelSerializer):
    """
    Serializer for RolePermission model.
    """
    permission = RBACPermissionSerializer(read_only=True)
    field_permission = FieldPermissionSerializer(read_only=True)
    permission_id = serializers.PrimaryKeyRelatedField(
        queryset=RBACPermission.objects.all(),
        source='permission',
        write_only=True,
        required=False,
        allow_null=True
    )
    field_permission_id = serializers.PrimaryKeyRelatedField(
        queryset=FieldPermission.objects.all(),
        source='field_permission',
        write_only=True,
        required=False,
        allow_null=True
    )
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    updated_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RolePermission
        fields = ('id', 'role', 'permission', 'field_permission', 'permission_id', 'field_permission_id', 'created_by', 'updated_by')
        read_only_fields = ('created_by', 'updated_by')

    def validate(self, data):
        """Validate that either permission or field_permission is provided."""
        permission = data.get('permission')
        field_permission = data.get('field_permission')
        if not permission and not field_permission:
            raise ValidationError('Either permission_id or field_permission_id must be provided.')
        if permission and field_permission:
            raise ValidationError('Cannot set both permission_id and field_permission_id.')
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['updated_by'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)

class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model."""
    role_permissions = RolePermissionSerializer(many=True, read_only=True)
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=RBACPermission.objects.all(),
        many=True,
        required=False,
        write_only=True
    )
    field_permissions = serializers.PrimaryKeyRelatedField(
        queryset=FieldPermission.objects.all(),
        many=True,
        required=False,
        write_only=True
    )

    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'role_permissions', 'permissions', 'field_permissions', 'created_by', 'updated_by', 'created_at', 'updated_at')
        read_only_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    def validate(self, data):
        """Validate the data."""
        # Make permissions and field_permissions optional
        return data

    def create(self, validated_data):
        """Create a new role with permissions."""
        permissions = validated_data.pop('permissions', [])
        field_permissions = validated_data.pop('field_permissions', [])
        user = self.context['request'].user
        
        # Set created_by and updated_by from validated_data or use the request user
        validated_data['created_by'] = validated_data.get('created_by', user)
        validated_data['updated_by'] = validated_data.get('updated_by', user)
        
        role = super().create(validated_data)
        
        # Create role permissions
        for permission in permissions:
            RolePermission.objects.create(
                role=role,
                permission=permission,
                created_by=user,
                updated_by=user
            )
        
        for field_permission in field_permissions:
            RolePermission.objects.create(
                role=role,
                field_permission=field_permission,
                created_by=user,
                updated_by=user
            )
        
        return role

    def update(self, instance, validated_data):
        """Update a role and its permissions."""
        permissions = validated_data.pop('permissions', None)
        field_permissions = validated_data.pop('field_permissions', None)
        user = self.context['request'].user
        validated_data['updated_by'] = user
        
        role = super().update(instance, validated_data)
        
        if permissions is not None:
            # Remove existing permissions
            RolePermission.objects.filter(role=role, permission__isnull=False).delete()
            # Add new permissions
            for permission in permissions:
                RolePermission.objects.create(
                    role=role,
                    permission=permission,
                    created_by=user,
                    updated_by=user
                )
        
        if field_permissions is not None:
            # Remove existing field permissions
            RolePermission.objects.filter(role=role, field_permission__isnull=False).delete()
            # Add new field permissions
            for field_permission in field_permissions:
                RolePermission.objects.create(
                    role=role,
                    field_permission=field_permission,
                    created_by=user,
                    updated_by=user
                )
        
        return role

class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model."""
    role_id = serializers.PrimaryKeyRelatedField(
        source='role',
        queryset=Role.objects.all(),
        write_only=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=User.objects.all(),
        write_only=True
    )
    role = RoleSerializer(read_only=True)
    user = serializers.SerializerMethodField()

    class Meta:
        model = UserRole
        fields = ('id', 'user', 'role', 'user_id', 'role_id', 'created_by', 'updated_by', 'created_at', 'updated_at')
        read_only_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    def get_user(self, obj):
        return obj.user.id

    def validate(self, data):
        """Validate the data."""
        user = data.get('user')
        role = data.get('role')
        
        # Check if user role already exists
        existing = UserRole.objects.filter(user=user, role=role)
        if self.instance:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise ValidationError('User role with this User and Role already exists.')
        
        return data

    def create(self, validated_data):
        """Create a new user role."""
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update a user role."""
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)

class FieldPermissionAvailableFieldsSerializer(serializers.Serializer):
    """Serializer for available fields for field permissions."""
    fields = serializers.ListField(child=serializers.CharField())

class RoleAssignPermissionsSerializer(serializers.Serializer):
    """Serializer for assigning permissions to roles."""
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=RBACPermission.objects.all(),
        many=True,
        required=False
    )
    field_permissions = serializers.PrimaryKeyRelatedField(
        queryset=FieldPermission.objects.all(),
        many=True,
        required=False
    )

    def validate(self, data):
        """Validate the data."""
        if not data.get('permissions') and not data.get('field_permissions'):
            raise ValidationError('Either permissions or field_permissions must be provided.')
        return data

class UserRoleMyRolesSerializer(serializers.ModelSerializer):
    """Serializer for user's roles."""
    role = RoleSerializer(read_only=True)

    class Meta:
        model = UserRole
        fields = ('id', 'role')

class UserRoleMyFieldPermissionsSerializer(serializers.ModelSerializer):
    """Serializer for user's field permissions."""
    permission = RBACPermissionSerializer(read_only=True)
    field_permission = FieldPermissionSerializer(read_only=True)

    class Meta:
        model = RolePermission
        fields = ('id', 'permission', 'field_permission') 