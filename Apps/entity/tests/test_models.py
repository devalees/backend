import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from Apps.entity.models import Organization, Department, Team, TeamMember
from Apps.entity.tests.factories import (
    OrganizationFactory, DepartmentFactory, TeamFactory, TeamMemberFactory
)

@pytest.mark.django_db
class TestOrganization:
    def test_create_organization(self):
        """Test creating an organization"""
        org = OrganizationFactory()
        assert org.name is not None
        assert org.description is not None
        assert org.created_by is not None
        assert org.is_active

    def test_organization_str(self):
        """Test string representation of organization"""
        org = OrganizationFactory()
        assert str(org) == org.name

    def test_organization_soft_delete(self):
        """Test soft delete functionality"""
        org = OrganizationFactory()
        org.delete()
        assert not org.is_active
        assert Organization.objects.filter(id=org.id).exists()

    def test_organization_hard_delete(self):
        """Test hard delete functionality"""
        org = OrganizationFactory()
        dept = DepartmentFactory(organization=org)
        team = TeamFactory(department=dept)
        
        org.hard_delete()
        assert not Organization.objects.filter(id=org.id).exists()
        assert not Department.objects.filter(id=dept.id).exists()
        assert not Team.objects.filter(id=team.id).exists()

    def test_organization_name_unique(self):
        """Test that organization names must be unique"""
        org1 = OrganizationFactory()
        with pytest.raises(ValidationError):
            org2 = OrganizationFactory(name=org1.name)
            org2.full_clean()

    def test_organization_name_max_length(self):
        """Test that organization names cannot exceed 255 characters"""
        with pytest.raises(ValidationError):
            org = OrganizationFactory(name='a' * 256)
            org.full_clean()

@pytest.mark.django_db
class TestDepartment:
    def test_create_department(self):
        """Test creating a department"""
        dept = DepartmentFactory()
        assert dept.name is not None
        assert dept.description is not None
        assert dept.organization is not None
        assert dept.created_by is not None
        assert dept.is_active

    def test_department_str(self):
        """Test string representation of department"""
        dept = DepartmentFactory()
        assert str(dept) == f"{dept.name} ({dept.organization.name})"

    def test_department_soft_delete(self):
        """Test soft delete functionality"""
        dept = DepartmentFactory()
        dept.delete()
        assert not dept.is_active
        assert Department.objects.filter(id=dept.id).exists()

    def test_department_hard_delete(self):
        """Test hard delete functionality and cascade"""
        dept = DepartmentFactory()
        child_dept = DepartmentFactory(parent=dept, organization=dept.organization)
        team = TeamFactory(department=dept)
        
        dept.hard_delete()
        assert not Department.objects.filter(id=dept.id).exists()
        assert not Department.objects.filter(id=child_dept.id).exists()
        assert not Team.objects.filter(id=team.id).exists()

    def test_department_organization_required(self):
        """Test that departments must have an organization"""
        with pytest.raises(IntegrityError):
            dept = Department(name="Test Department")
            dept.save()

    def test_department_unique_name_per_org(self):
        """Test that department names must be unique within an organization"""
        dept1 = DepartmentFactory()
        with pytest.raises(ValidationError):
            dept2 = DepartmentFactory(name=dept1.name, organization=dept1.organization)
            dept2.full_clean()

    def test_department_parent_same_org(self):
        """Test that parent department must be in same organization"""
        dept1 = DepartmentFactory()
        org2 = OrganizationFactory()
        with pytest.raises(ValidationError):
            dept2 = DepartmentFactory(parent=dept1, organization=org2)
            dept2.full_clean()

    def test_department_circular_reference(self):
        """Test prevention of circular references in department hierarchy"""
        dept1 = DepartmentFactory()
        dept2 = DepartmentFactory(parent=dept1, organization=dept1.organization)
        
        with pytest.raises(ValidationError):
            dept1.parent = dept2
            dept1.full_clean()

@pytest.mark.django_db
class TestTeam:
    def test_create_team(self):
        """Test creating a team"""
        team = TeamFactory()
        assert team.name is not None
        assert team.description is not None
        assert team.department is not None
        assert team.created_by is not None
        assert team.is_active

    def test_team_str(self):
        """Test string representation of team"""
        team = TeamFactory()
        assert str(team) == f"{team.name} ({team.department.name})"

    def test_team_soft_delete(self):
        """Test soft delete functionality"""
        team = TeamFactory()
        team.delete()
        assert not team.is_active
        assert Team.objects.filter(id=team.id).exists()

    def test_team_hard_delete(self):
        """Test hard delete functionality"""
        team = TeamFactory()
        member = TeamMemberFactory(team=team)
        
        team.hard_delete()
        assert not Team.objects.filter(id=team.id).exists()
        assert not TeamMember.objects.filter(id=member.id).exists()

    def test_team_unique_name_per_department(self):
        """Test that team names must be unique within a department"""
        team1 = TeamFactory()
        with pytest.raises(ValidationError):
            team2 = TeamFactory(name=team1.name, department=team1.department)
            team2.full_clean()

    def test_team_parent_same_department(self):
        """Test that parent team must be in same department"""
        team1 = TeamFactory()
        dept2 = DepartmentFactory(organization=team1.department.organization)
        with pytest.raises(ValidationError):
            team2 = TeamFactory(parent=team1, department=dept2)
            team2.full_clean()

@pytest.mark.django_db
class TestTeamMember:
    def test_create_team_member(self):
        """Test creating a team member"""
        member = TeamMemberFactory()
        assert member.user is not None
        assert member.team is not None
        assert member.role is not None
        assert member.created_by is not None
        assert member.is_active

    def test_team_member_str(self):
        """Test string representation of team member"""
        member = TeamMemberFactory()
        assert str(member) == f"{member.user.username} - {member.team.name} ({member.role})"

    def test_team_member_soft_delete(self):
        """Test soft delete functionality"""
        member = TeamMemberFactory()
        member.delete()
        assert not member.is_active
        assert TeamMember.objects.filter(id=member.id).exists()

    def test_team_member_hard_delete(self):
        """Test hard delete functionality"""
        member = TeamMemberFactory()
        member.hard_delete()
        assert not TeamMember.objects.filter(id=member.id).exists()

    def test_unique_user_team_constraint(self):
        """Test that a user cannot be added to the same team twice"""
        member = TeamMemberFactory()
        with pytest.raises(ValidationError):
            TeamMemberFactory(user=member.user, team=member.team)

    def test_team_member_role_default(self):
        """Test that team member role defaults to 'Member'"""
        member = TeamMemberFactory()
        assert member.role == 'Member' 