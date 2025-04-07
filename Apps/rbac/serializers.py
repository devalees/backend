from rest_framework import serializers
from .models import UserRole, Role, Permission
from Apps.users.models import User

class UserRoleSerializer(serializers.ModelSerializer):
    """Serializer for UserRole model"""
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())
    assigned_by = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    delegated_by = serializers.PrimaryKeyRelatedField(
        queryset=UserRole.objects.all(),
        required=False,
        allow_null=True
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

class RoleSerializer(serializers.ModelSerializer):
    """Serializer for Role model"""
    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'organization', 'parent',
            'is_active', 'created_at', 'updated_at'
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

class PermissionSerializer(serializers.ModelSerializer):
    """Serializer for Permission model"""
    class Meta:
        model = Permission
        fields = [
            'id', 'name', 'description', 'code', 'organization',
            'created_at', 'updated_at'
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