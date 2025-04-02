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

class RBACPermissionSerializer(serializers.ModelSerializer):
    """Serializer for RBACPermission model."""
    content_type = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all())

    class Meta:
        model = RBACPermission
        fields = ('id', 'content_type', 'codename', 'name')

class FieldPermissionSerializer(serializers.ModelSerializer):
    """Serializer for FieldPermission model."""
    content_type = serializers.SerializerMethodField()

    class Meta:
        model = FieldPermission
        fields = ('id', 'content_type', 'field_name', 'permission_type')

    def get_content_type(self, obj):
        return {
            'id': obj.content_type.id,
            'app_label': obj.content_type.app_label,
            'model': obj.content_type.model
        }

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
        required=False
    )
    field_permission_id = serializers.PrimaryKeyRelatedField(
        queryset=FieldPermission.objects.all(),
        source='field_permission',
        write_only=True,
        required=False
    )

    class Meta:
        model = RolePermission
        fields = ('id', 'role', 'permission', 'field_permission', 'permission_id', 'field_permission_id', 'created_by', 'updated_by', 'created_at', 'updated_at')
        read_only_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    def validate(self, data):
        """Validate that either permission or field_permission is provided."""
        if not data.get('permission') and not data.get('field_permission'):
            raise ValidationError(_('Either permission or field_permission must be provided.'))
        if data.get('permission') and data.get('field_permission'):
            raise ValidationError(_('Cannot set both permission and field_permission.'))
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

    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'role_permissions', 'created_by', 'updated_by', 'created_at', 'updated_at')
        read_only_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)

class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model."""
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source='role',
        write_only=True
    )

    class Meta:
        model = UserRole
        fields = ('id', 'user', 'role', 'role_id', 'created_by', 'updated_by')
        read_only_fields = ('created_by', 'updated_by')

    def create(self, validated_data):
        """Create a new user role."""
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['updated_by'] = user
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