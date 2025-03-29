from rest_framework import serializers
from .models import Organization, Department, Team, TeamMember
from rest_framework.validators import UniqueTogetherValidator
from django.contrib.auth import get_user_model

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