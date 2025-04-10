import pytest
from django.core.exceptions import ValidationError
from Apps.rbac.serializers import RoleSerializer, PermissionSerializer
from Apps.rbac.models import Role, Permission
from Apps.entity.models import Organization

@pytest.mark.django_db
class TestRoleValidation:
    def test_role_name_validation(self, organization):
        # Test empty name
        data = {
            'name': '',
            'description': 'Test Role',
            'organization': organization.id
        }
        serializer = RoleSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

        # Test name too short
        data['name'] = 'ab'
        serializer = RoleSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

        # Test name too long
        data['name'] = 'a' * 101
        serializer = RoleSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

        # Test valid name
        data['name'] = 'Test Role'
        serializer = RoleSerializer(data=data)
        assert serializer.is_valid()

    def test_role_description_validation(self, organization):
        # Test description too long
        data = {
            'name': 'Test Role',
            'description': 'a' * 501,
            'organization': organization.id
        }
        serializer = RoleSerializer(data=data)
        assert not serializer.is_valid()
        assert 'description' in serializer.errors

        # Test valid description
        data['description'] = 'Test Description'
        serializer = RoleSerializer(data=data)
        assert serializer.is_valid()

    def test_role_duplicate_name_validation(self, organization):
        # Create initial role
        Role.objects.create(
            name='Test Role',
            description='Test Description',
            organization=organization
        )

        # Try to create role with same name
        data = {
            'name': 'Test Role',
            'description': 'Another Description',
            'organization': organization.id
        }
        serializer = RoleSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors

@pytest.mark.django_db
class TestPermissionValidation:
    def test_permission_name_validation(self, organization):
        # Test empty name
        data = {
            'name': '',
            'description': 'Test Permission',
            'code': 'test.permission',
            'organization': organization.id
        }
        serializer = PermissionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

        # Test name too short
        data['name'] = 'ab'
        serializer = PermissionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

        # Test name too long
        data['name'] = 'a' * 101
        serializer = PermissionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'name' in serializer.errors

        # Test valid name
        data['name'] = 'Test Permission'
        serializer = PermissionSerializer(data=data)
        assert serializer.is_valid()

    def test_permission_code_validation(self, organization):
        # Test invalid code format
        data = {
            'name': 'Test Permission',
            'description': 'Test Description',
            'code': 'test@permission',
            'organization': organization.id
        }
        serializer = PermissionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'code' in serializer.errors

        # Test code too short
        data['code'] = 'a'
        serializer = PermissionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'code' in serializer.errors

        # Test code too long
        data['code'] = 'a' * 101
        serializer = PermissionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'code' in serializer.errors

        # Test valid code
        data['code'] = 'test.permission'
        serializer = PermissionSerializer(data=data)
        assert serializer.is_valid()

    def test_permission_duplicate_validation(self, organization):
        # Create initial permission
        Permission.objects.create(
            name='Test Permission',
            description='Test Description',
            code='test.permission',
            organization=organization
        )

        # Try to create permission with same code
        data = {
            'name': 'Another Permission',
            'description': 'Another Description',
            'code': 'test.permission',
            'organization': organization.id
        }
        serializer = PermissionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors

        # Try to create permission with same name
        data['code'] = 'another.permission'
        data['name'] = 'Test Permission'
        serializer = PermissionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors 