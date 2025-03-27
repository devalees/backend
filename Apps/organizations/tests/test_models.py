import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from Apps.organizations.models import Organization, Department, Team, TeamMember
from Apps.users.models import User

User = get_user_model()

@pytest.mark.django_db
class TestOrganizationModel:
    def test_create_organization(self):
        """Test creating a new organization"""
        org = Organization.objects.create(
            name='Test Organization',
            description='Test Description'
        )
        assert org.name == 'Test Organization'
        assert org.description == 'Test Description'
        assert org.is_active
        assert str(org) == 'Test Organization'

    def test_organization_unique_name(self):
        """Test that organization names must be unique"""
        Organization.objects.create(name='Test Org')
        org2 = Organization(name='Test Org')
        with pytest.raises(ValidationError):
            org2.full_clean()

    def test_organization_soft_delete(self):
        """Test organization soft delete functionality"""
        org = Organization.objects.create(name='Test Org')
        assert org.is_active
        org.delete()
        assert not org.is_active
        assert Organization.objects.filter(name='Test Org').exists()

@pytest.mark.django_db
class TestDepartmentModel:
    @pytest.fixture
    def organization(self):
        return Organization.objects.create(name='Test Org')

    def test_create_department(self, organization):
        """Test creating a new department"""
        dept = Department.objects.create(
            name='Engineering',
            organization=organization,
            description='Engineering Department'
        )
        assert dept.name == 'Engineering'
        assert dept.organization == organization
        assert dept.description == 'Engineering Department'
        assert dept.is_active
        assert str(dept) == 'Engineering'

    def test_department_unique_name_per_organization(self, organization):
        """Test that department names must be unique within an organization"""
        Department.objects.create(name='Engineering', organization=organization)
        dept2 = Department(name='Engineering', organization=organization)
        with pytest.raises(ValidationError):
            dept2.full_clean()

    def test_department_same_name_different_organizations(self):
        """Test that departments can have same name in different organizations"""
        org1 = Organization.objects.create(name='Org 1')
        org2 = Organization.objects.create(name='Org 2')
        dept1 = Department.objects.create(name='Engineering', organization=org1)
        dept2 = Department.objects.create(name='Engineering', organization=org2)
        assert dept1.name == dept2.name
        assert dept1.organization != dept2.organization

@pytest.mark.django_db
class TestTeamModel:
    @pytest.fixture
    def organization(self):
        return Organization.objects.create(name='Test Org')

    @pytest.fixture
    def department(self, organization):
        return Department.objects.create(name='Engineering', organization=organization)

    def test_create_team(self, department):
        """Test creating a new team"""
        team = Team.objects.create(
            name='Frontend Team',
            department=department,
            description='Frontend Development Team'
        )
        assert team.name == 'Frontend Team'
        assert team.department == department
        assert team.description == 'Frontend Development Team'
        assert team.is_active
        assert str(team) == 'Frontend Team'

    def test_team_unique_name_per_department(self, department):
        """Test that team names must be unique within a department"""
        Team.objects.create(name='Frontend', department=department)
        team2 = Team(name='Frontend', department=department)
        with pytest.raises(ValidationError):
            team2.full_clean()

    def test_team_same_name_different_departments(self, organization):
        """Test that teams can have same name in different departments"""
        dept1 = Department.objects.create(name='Engineering', organization=organization)
        dept2 = Department.objects.create(name='Design', organization=organization)
        team1 = Team.objects.create(name='Frontend', department=dept1)
        team2 = Team.objects.create(name='Frontend', department=dept2)
        assert team1.name == team2.name
        assert team1.department != team2.department

@pytest.mark.django_db
class TestTeamMemberModel:
    @pytest.fixture
    def organization(self):
        return Organization.objects.create(name='Test Org')

    @pytest.fixture
    def department(self, organization):
        return Department.objects.create(name='Engineering', organization=organization)

    @pytest.fixture
    def team(self, department):
        return Team.objects.create(name='Frontend', department=department)

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_team_member(self, team, user):
        """Test creating a new team member"""
        member = TeamMember.objects.create(
            team=team,
            user=user,
            role='Developer'
        )
        assert member.team == team
        assert member.user == user
        assert member.role == 'Developer'
        assert member.is_active
        assert str(member) == f'{user.username} - {team.name} (Developer)'

    def test_team_member_unique_user_per_team(self, team, user):
        """Test that a user can only be a member of a team once"""
        TeamMember.objects.create(team=team, user=user, role='Developer')
        member2 = TeamMember(team=team, user=user, role='Senior Developer')
        with pytest.raises(ValidationError):
            member2.full_clean()

    def test_team_member_same_user_different_teams(self, department, user):
        """Test that a user can be a member of different teams"""
        team1 = Team.objects.create(name='Frontend', department=department)
        team2 = Team.objects.create(name='Backend', department=department)
        member1 = TeamMember.objects.create(team=team1, user=user, role='Developer')
        member2 = TeamMember.objects.create(team=team2, user=user, role='Developer')
        assert member1.user == member2.user
        assert member1.team != member2.team

    def test_team_member_soft_delete(self, team, user):
        """Test team member soft delete functionality"""
        member = TeamMember.objects.create(team=team, user=user, role='Developer')
        assert member.is_active
        member.delete()
        assert not member.is_active
        assert TeamMember.objects.filter(team=team, user=user).exists()
