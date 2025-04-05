from rest_framework import serializers
from .models import Organization, Department, Team, TeamMember, OrganizationSettings
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth import get_user_model
import pytz

User = get_user_model()

class SimpleUserSerializer(serializers.ModelSerializer):
    """Simplified serializer for User model in team member context"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        read_only_fields = fields

class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model"""
    class Meta:
        model = Organization
        fields = ('id', 'name', 'description', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model"""
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = Department
        fields = ('id', 'name', 'description', 'organization', 'organization_name', 'parent', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team model"""
    department_name = serializers.CharField(source='department.name', read_only=True)

    class Meta:
        model = Team
        fields = ('id', 'name', 'description', 'department', 'department_name', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for TeamMember model"""
    user = SimpleUserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True
    )
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = TeamMember
        fields = ('id', 'user', 'user_id', 'team', 'team_name', 'role', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate(self, data):
        """Validate that a user is not already a member of the team"""
        user = data.get('user_id')
        team = data.get('team')
        if user and team:
            if TeamMember.objects.filter(user=user, team=team).exists():
                raise serializers.ValidationError("This user is already a member of this team.")
        return data

    def create(self, validated_data):
        """Create a new team member"""
        user = validated_data.pop('user_id')
        validated_data['user'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update a team member"""
        if 'user_id' in validated_data:
            user = validated_data.pop('user_id')
            validated_data['user'] = user
        return super().update(instance, validated_data)

class OrganizationSettingsSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationSettings model"""
    class Meta:
        model = OrganizationSettings
        fields = [
            'id',
            'organization',
            'timezone',
            'date_format',
            'time_format',
            'language',
            'notification_preferences',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_timezone(self, value):
        """Validate timezone"""
        if value not in pytz.all_timezones:
            raise serializers.ValidationError("Invalid timezone")
        return value

    def validate_date_format(self, value):
        """Validate date format"""
        valid_formats = ['YYYY-MM-DD', 'MM/DD/YYYY', 'DD/MM/YYYY']
        if value not in valid_formats:
            raise serializers.ValidationError("Invalid date format")
        return value

    def validate_time_format(self, value):
        """Validate time format"""
        valid_formats = ['12h', '24h']
        if value not in valid_formats:
            raise serializers.ValidationError("Invalid time format")
        return value

    def validate_language(self, value):
        """Validate language"""
        valid_languages = ['en', 'es', 'fr', 'de']
        if value not in valid_languages:
            raise serializers.ValidationError("Invalid language")
        return value

    def validate_notification_preferences(self, value):
        """Validate notification preferences"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Notification preferences must be a dictionary")
        
        required_keys = ['email', 'push', 'slack']
        for key in required_keys:
            if key not in value:
                raise serializers.ValidationError(f"Missing required key: {key}")
            if not isinstance(value[key], bool):
                raise serializers.ValidationError(f"Value for {key} must be boolean")
        
        return value 