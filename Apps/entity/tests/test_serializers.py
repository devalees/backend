import pytest
from django.core.exceptions import ValidationError
from Apps.entity.serializers import (
    OrganizationSerializer, DepartmentSerializer,
    TeamSerializer, TeamMemberSerializer
)
from Apps.entity.tests.factories import (
    OrganizationFactory, DepartmentFactory,
    TeamFactory, TeamMemberFactory
)
from Apps.users.tests.factories import UserFactory

@pytest.mark.django_db
class TestOrganizationSerializer:
    def test_serialize_organization(self):
        """Test serializing an organization"""
        org = OrganizationFactory()
        serializer = OrganizationSerializer(org)
        
        assert serializer.data['name'] == org.name
        assert serializer.data['description'] == org.description
        assert serializer.data['is_active']
        assert 'created_at' in serializer.data
        assert 'updated_at' in serializer.data

    def test_deserialize_valid_data(self):
        """Test deserializing valid organization data"""
        data = {
            'name': 'Test Organization',
            'description': 'Test Description'
        }
        serializer = OrganizationSerializer(data=data)
        
        assert serializer.is_valid()
        org = serializer.save()
        assert org.name == data['name']
        assert org.description == data['description']

    def test_deserialize_invalid_data(self):
        """Test deserializing invalid organization data"""
        data = {
            'name': 'a' * 256,  # Name too long
            'description': 'Test Description'
        }
        serializer = OrganizationSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

@pytest.mark.django_db
class TestDepartmentSerializer:
    def test_serialize_department(self):
        """Test serializing a department"""
        dept = DepartmentFactory()
        serializer = DepartmentSerializer(dept)
        
        assert serializer.data['name'] == dept.name
        assert serializer.data['description'] == dept.description
        assert serializer.data['organization'] == dept.organization.pk
        assert serializer.data['organization_name'] == dept.organization.name
        assert serializer.data['is_active']
        assert 'created_at' in serializer.data
        assert 'updated_at' in serializer.data

    def test_deserialize_valid_data(self):
        """Test deserializing valid department data"""
        org = OrganizationFactory()
        data = {
            'name': 'Test Department',
            'description': 'Test Description',
            'organization': org.pk
        }
        serializer = DepartmentSerializer(data=data)
        
        assert serializer.is_valid()
        dept = serializer.save()
        assert dept.name == data['name']
        assert dept.organization == org

    def test_deserialize_invalid_data(self):
        """Test deserializing invalid department data"""
        data = {
            'name': 'Test Department',
            'description': 'Test Description',
            'organization': 999  # Non-existent organization
        }
        serializer = DepartmentSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'organization' in serializer.errors

@pytest.mark.django_db
class TestTeamSerializer:
    def test_serialize_team(self):
        """Test serializing a team"""
        team = TeamFactory()
        serializer = TeamSerializer(team)
        
        assert serializer.data['name'] == team.name
        assert serializer.data['description'] == team.description
        assert serializer.data['department'] == team.department.pk
        assert serializer.data['department_name'] == team.department.name
        assert serializer.data['is_active']
        assert 'created_at' in serializer.data
        assert 'updated_at' in serializer.data

    def test_deserialize_valid_data(self):
        """Test deserializing valid team data"""
        dept = DepartmentFactory()
        data = {
            'name': 'Test Team',
            'description': 'Test Description',
            'department': dept.pk
        }
        serializer = TeamSerializer(data=data)
        
        assert serializer.is_valid()
        team = serializer.save()
        assert team.name == data['name']
        assert team.department == dept

    def test_deserialize_invalid_data(self):
        """Test deserializing invalid team data"""
        data = {
            'name': 'Test Team',
            'description': 'Test Description',
            'department': 999  # Non-existent department
        }
        serializer = TeamSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'department' in serializer.errors

@pytest.mark.django_db
class TestTeamMemberSerializer:
    def test_serialize_team_member(self):
        """Test serializing a team member"""
        member = TeamMemberFactory()
        serializer = TeamMemberSerializer(member)
        
        assert serializer.data['team'] == member.team.pk
        assert serializer.data['team_name'] == member.team.name
        assert serializer.data['role'] == member.role
        assert serializer.data['is_active']
        assert 'created_at' in serializer.data
        assert 'updated_at' in serializer.data

    def test_deserialize_valid_data(self):
        """Test deserializing valid team member data"""
        team = TeamFactory()
        user = UserFactory()
        data = {
            'team': team.pk,
            'user_id': user.pk,
            'role': 'Leader'
        }
        serializer = TeamMemberSerializer(data=data)
        
        assert serializer.is_valid()
        member = serializer.save()
        assert member.team == team
        assert member.user == user
        assert member.role == data['role']

    def test_deserialize_invalid_data(self):
        """Test deserializing invalid team member data"""
        data = {
            'team': 999,  # Non-existent team
            'user_id': 999,  # Non-existent user
            'role': 'Invalid Role'
        }
        serializer = TeamMemberSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'team' in serializer.errors
        assert 'user_id' in serializer.errors

    def test_unique_user_team_constraint(self):
        """Test that a user cannot be added to the same team twice"""
        member = TeamMemberFactory()
        data = {
            'team': member.team.pk,
            'user_id': member.user.pk,
            'role': 'Member'
        }
        serializer = TeamMemberSerializer(data=data)
        
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors 