from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Role, Permission, RolePermission, UserRole, FieldPermission
from django.db.utils import IntegrityError
import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()

class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']

class FieldPermissionSerializer(serializers.ModelSerializer):
    # Use ContentTypeSerializer for READ operations only
    content_type = ContentTypeSerializer(read_only=True)
    # Accept an integer ID for WRITE operations
    content_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all(),
        source='content_type', # Map this input to the 'content_type' model field
        write_only=True,
        label="Content Type ID"
    )

    class Meta:
        model = FieldPermission
        # Include both fields in Meta, one read_only, one write_only
        fields = ['id', 'content_type', 'content_type_id', 'field_name', 'permission_type', 'description',
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        # 'content_type' is already populated correctly by PrimaryKeyRelatedField
        # We just need to set created_by/updated_by
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # 'content_type' will be updated automatically if 'content_type_id' is in validated_data
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)

class PermissionSerializer(serializers.ModelSerializer):
    # Use ContentTypeSerializer for READ operations only
    content_type = ContentTypeSerializer(read_only=True)
    # Accept a dictionary for WRITE operations
    content_type_input = serializers.DictField(
        child=serializers.CharField(),
        write_only=True,
        help_text="Dict with 'app_label' and 'model'",
        label="Content Type Input"
    )

    class Meta:
        model = Permission
        # Include both fields in Meta, one read_only, one write_only
        fields = ['id', 'name', 'codename', 'content_type', 'content_type_input', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        logger.debug(f"PermissionSerializer.create called with validated_data: {validated_data}")
        # Pop the dictionary from the 'content_type_input' field
        content_type_data = validated_data.pop('content_type_input')
        logger.debug(f"Attempting to find ContentType for: {content_type_data}")
        try:
            # Validate the input dictionary structure
            app_label = content_type_data.get('app_label')
            model = content_type_data.get('model')
            if not app_label or not model:
                raise serializers.ValidationError({
                    'content_type_input': "Dictionary must contain 'app_label' and 'model' keys."
                })
            
            content_type = ContentType.objects.get(
                app_label=app_label,
                model=model
            )
            logger.debug(f"Found ContentType: {content_type}")
        except ContentType.DoesNotExist:
            logger.error(f"ContentType lookup failed for: {content_type_data}")
            raise serializers.ValidationError({
                'content_type_input': f'Content type {content_type_data} does not exist.'
            })

        try:
            permission = Permission.objects.create(content_type=content_type, **validated_data)
            logger.debug(f"Successfully created Permission: {permission}")
            return permission
        except IntegrityError as e:
            logger.error(f"IntegrityError during Permission creation: {e}")
            raise serializers.ValidationError(f"Failed to create permission due to constraint violation: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during Permission creation: {e}")
            raise serializers.ValidationError(f"An unexpected error occurred: {e}")

    def update(self, instance, validated_data):
        if 'content_type' in validated_data:
            content_type_data = validated_data.pop('content_type')
            try:
                content_type = ContentType.objects.get(
                    app_label=content_type_data['app_label'],
                    model=content_type_data['model']
                )
                validated_data['content_type'] = content_type
            except ContentType.DoesNotExist:
                raise serializers.ValidationError({
                    'content_type': f"Content type with app_label='{content_type_data['app_label']}' and model='{content_type_data['model']}' does not exist."
                })
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)

class RoleSerializer(serializers.ModelSerializer):
    """
    Serializer for Role model.
    """
    permissions = serializers.SerializerMethodField()
    field_permissions = serializers.SerializerMethodField()
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    field_permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'field_permissions',
                 'permission_ids', 'field_permission_ids', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_permissions(self, obj):
        role_permissions = obj.role_permissions.filter(field_permission__isnull=True)
        permissions = [rp.permission for rp in role_permissions]
        return PermissionSerializer(permissions, many=True).data

    def get_field_permissions(self, obj):
        role_permissions = obj.role_permissions.filter(field_permission__isnull=False)
        field_permissions = [rp.field_permission for rp in role_permissions]
        return FieldPermissionSerializer(field_permissions, many=True).data

    def create(self, validated_data):
        permission_ids = validated_data.pop('permission_ids', [])
        field_permission_ids = validated_data.pop('field_permission_ids', [])
        validated_data['created_by'] = self.context['request'].user
        validated_data['updated_by'] = self.context['request'].user
        role = super().create(validated_data)
        
        # Add permissions
        for permission_id in permission_ids:
            try:
                permission = Permission.objects.get(id=permission_id)
                RolePermission.objects.create(
                    role=role,
                    permission=permission,
                    created_by=self.context['request'].user
                )
            except Permission.DoesNotExist:
                continue
        
        # Add field permissions
        for field_permission_id in field_permission_ids:
            try:
                field_permission = FieldPermission.objects.get(id=field_permission_id)
                permission = Permission.objects.get(codename=field_permission.permission_type)
                RolePermission.objects.create(
                    role=role,
                    permission=permission,
                    field_permission=field_permission,
                    created_by=self.context['request'].user
                )
            except (FieldPermission.DoesNotExist, Permission.DoesNotExist):
                continue
        
        return role

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop('permission_ids', None)
        field_permission_ids = validated_data.pop('field_permission_ids', None)
        validated_data['updated_by'] = self.context['request'].user
        role = super().update(instance, validated_data)
        
        if permission_ids is not None:
            # Remove existing permissions
            instance.role_permissions.filter(field_permission__isnull=True).delete()
            
            # Add new permissions
            for permission_id in permission_ids:
                try:
                    permission = Permission.objects.get(id=permission_id)
                    RolePermission.objects.create(
                        role=role,
                        permission=permission,
                        created_by=self.context['request'].user
                    )
                except Permission.DoesNotExist:
                    continue
        
        if field_permission_ids is not None:
            # Remove existing field permissions
            instance.role_permissions.filter(field_permission__isnull=False).delete()
            
            # Add new field permissions
            for field_permission_id in field_permission_ids:
                try:
                    field_permission = FieldPermission.objects.get(id=field_permission_id)
                    permission = Permission.objects.get(codename=field_permission.permission_type)
                    RolePermission.objects.create(
                        role=role,
                        permission=permission,
                        field_permission=field_permission,
                        created_by=self.context['request'].user
                    )
                except (FieldPermission.DoesNotExist, Permission.DoesNotExist):
                    continue
        
        return role

class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'permission', 'field_permission', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class UserRoleSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source='role',
        write_only=True
    )

    class Meta:
        model = UserRole
        fields = ['id', 'user', 'role', 'role_id', 'created_at']
        read_only_fields = ['created_at'] 