import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from Apps.rbac.models import UserRole, Role
from Apps.users.models import User
from Apps.entity.models import Organization, Team, TeamMember, Department

@pytest.mark.django_db
class TestUserRole:
    def test_create_user_role(self, organization, user, role):
        """Test creating a basic user role assignment"""
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            organization=organization,
            assigned_by=user,
            is_active=True
        )
        assert user_role.user == user
        assert user_role.role == role
        assert user_role.organization == organization
        assert user_role.is_active is True

    def test_user_role_unique_constraint(self, organization, user, role):
        """Test that a user can't have the same role twice in the same organization"""
        UserRole.objects.create(
            user=user,
            role=role,
            organization=organization,
            assigned_by=user
        )
        with pytest.raises(ValidationError):
            UserRole.objects.create(
                user=user,
                role=role,
                organization=organization,
                assigned_by=user
            )

    def test_user_role_deactivation(self, organization, user, role):
        """Test deactivating a user role"""
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            organization=organization,
            assigned_by=user
        )
        user_role.deactivate()
        assert user_role.is_active is False
        assert user_role.deactivated_at is not None

    def test_user_role_reactivation(self, organization, user, role):
        """Test reactivating a deactivated user role"""
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            organization=organization,
            assigned_by=user
        )
        user_role.deactivate()
        user_role.activate()
        assert user_role.is_active is True
        assert user_role.deactivated_at is None

    def test_user_role_caching(self, organization, user, role, common_permissions):
        """Test caching of user role permissions"""
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            organization=organization,
            assigned_by=user
        )
        # Add some permissions to the role
        role.permissions.add(common_permissions['view_project'])
        role.permissions.add(common_permissions['edit_project'])
        
        # Test permission caching
        assert user_role.has_permission('view_project') is True
        assert user_role.has_permission('edit_project') is True
        assert user_role.has_permission('delete_project') is False

    def test_user_role_delegation(self, organization, user, role):
        """Test role delegation functionality"""
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            organization=organization,
            assigned_by=user
        )
    
        # Create another user for delegation
        delegated_user = User.objects.create(
            username='delegated_user',
            email='delegated@example.com',
            password='testpass123'
        )
    
        # Create a department and team, then add the delegated user to it
        department = Department.objects.create(
            name='Delegation Test Department',
            organization=organization
        )
        team = Team.objects.create(
            name='Delegation Test Team',
            department=department
        )
        TeamMember.objects.create(
            team=team,
            user=delegated_user,
            role=TeamMember.Role.MEMBER,
            is_active=True
        )
    
        # Create a delegated role
        delegated_role = UserRole.objects.create(
            user=delegated_user,
            role=role,
            organization=organization,
            assigned_by=user,
            delegated_by=user_role
        )
    
        # Verify delegation
        assert delegated_role.delegated_by == user_role
        assert delegated_role.is_delegated is True

    def test_user_role_conflict_resolution(self, organization, user, role):
        """Test role conflict resolution"""
        # Create a parent role
        parent_role = Role.objects.create(
            name='Parent Role',
            organization=organization
        )
        
        # Create a child role
        child_role = Role.objects.create(
            name='Child Role',
            organization=organization,
            parent=parent_role
        )
        
        # Assign both roles to user
        parent_user_role = UserRole.objects.create(
            user=user,
            role=parent_role,
            organization=organization,
            assigned_by=user
        )
        
        child_user_role = UserRole.objects.create(
            user=user,
            role=child_role,
            organization=organization,
            assigned_by=user
        )
        
        # Test conflict resolution
        assert child_user_role.has_higher_priority_than(parent_user_role) is True

    def test_user_role_clean_method(self, organization, user, role):
        """Test validation in clean method"""
        # Test invalid organization
        with pytest.raises(ValidationError):
            different_org = Organization.objects.create(name='Different Org')
            UserRole.objects.create(
                user=user,
                role=role,
                organization=different_org,
                assigned_by=user
            ).clean()

    def test_user_role_str_method(self, organization, user, role):
        """Test string representation of user role"""
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            organization=organization,
            assigned_by=user
        )
        expected_str = f"{user.username} - {role.name} ({organization.name})"
        assert str(user_role) == expected_str

    def test_user_role_permission_inheritance(self, organization, user, role, common_permissions):
        """Test permission inheritance through role hierarchy"""
        # Create a parent role with permissions
        parent_role = Role.objects.create(
            name='Parent Role',
            organization=organization
        )
        parent_role.permissions.add(common_permissions['view_project'])
        
        # Create a child role
        child_role = Role.objects.create(
            name='Child Role',
            organization=organization,
            parent=parent_role
        )
        child_role.permissions.add(common_permissions['edit_project'])
        
        # Assign child role to user
        user_role = UserRole.objects.create(
            user=user,
            role=child_role,
            organization=organization,
            assigned_by=user
        )
        
        # Test inherited permissions
        assert user_role.has_permission('view_project') is True
        assert user_role.has_permission('edit_project') is True 