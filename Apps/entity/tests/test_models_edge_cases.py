import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from Apps.entity.models import Organization, Department, Team, TeamMember
from Apps.users.models import User

@pytest.mark.django_db
class TestOrganizationModelEdgeCases:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def organization(self, user):
        return Organization.objects.create(
            name="Test Org",
            created_by=user
        )

    @pytest.fixture
    def department(self, organization, user):
        return Department.objects.create(
            name="Test Dept",
            organization=organization,
            created_by=user
        )

    @pytest.fixture
    def team(self, department, user):
        return Team.objects.create(
            name="Test Team",
            department=department,
            created_by=user
        )

    def test_organization_unique_name_validation(self, user):
        """Test that organization names must be unique"""
        Organization.objects.create(
            name="Test Org",
            created_by=user
        )
        with pytest.raises(ValidationError) as exc_info:
            Organization.objects.create(
                name="Test Org",
                created_by=user
            )
        assert "Entity with this Name already exists" in str(exc_info.value)

    def test_department_inactive_entity(self, organization, user):
        """Test that departments cannot be created for inactive entities"""
        organization.is_active = False
        organization.save()
        with pytest.raises(ValidationError) as exc_info:
            Department.objects.create(
                name="Test Dept",
                organization=organization,
                created_by=user
            )
        assert "Cannot create department for inactive organization" in str(exc_info.value)

    def test_department_unique_name_in_organization(self, organization, user):
        """Test that department names must be unique within an organization"""
        Department.objects.create(
            name="Test Dept",
            organization=organization,
            created_by=user
        )
        with pytest.raises(ValidationError) as exc_info:
            Department.objects.create(
                name="Test Dept",
                organization=organization,
                created_by=user
            )
        assert "A department with this name already exists in this organization" in str(exc_info.value)

    def test_department_parent_different_entity(self, organization, user):
        """Test that departments cannot have parents from different entities"""
        parent_dept = Department.objects.create(
            name="Parent Dept",
            organization=organization,
            created_by=user
        )
        other_org = Organization.objects.create(
            name="Other Org",
            created_by=user
        )
        child_dept = Department.objects.create(
            name="Child Dept",
            organization=other_org,
            created_by=user
        )
        with pytest.raises(ValidationError) as exc_info:
            child_dept.parent = parent_dept
            child_dept.save()
        assert "Parent department must belong to the same organization" in str(exc_info.value)

    def test_department_self_parent(self, organization, user):
        """Test that departments cannot be their own parent"""
        dept = Department.objects.create(
            name="Test Dept",
            organization=organization,
            created_by=user
        )
        with pytest.raises(ValidationError) as exc_info:
            dept.parent = dept
            dept.save()
        assert "Department cannot be its own parent" in str(exc_info.value)

    def test_department_circular_reference(self, organization, user):
        """Test that departments cannot create circular references"""
        dept1 = Department.objects.create(
            name="Dept 1",
            organization=organization,
            created_by=user
        )
        dept2 = Department.objects.create(
            name="Dept 2",
            organization=organization,
            parent=dept1,
            created_by=user
        )
        dept3 = Department.objects.create(
            name="Dept 3",
            organization=organization,
            parent=dept2,
            created_by=user
        )
        
        with pytest.raises(ValidationError) as exc_info:
            dept1.parent = dept3
            dept1.save()
        assert "Circular reference detected in department hierarchy" in str(exc_info.value)

    def test_department_max_hierarchy_depth(self, organization, user):
        """Test that departments cannot exceed maximum hierarchy depth"""
        parent = None
        for i in range(5):  # Create 5 levels
            dept = Department.objects.create(
                name=f"Dept {i}",
                organization=organization,
                parent=parent,
                created_by=user
            )
            parent = dept
        
        with pytest.raises(ValidationError) as exc_info:
            dept = Department(
                name="Too Deep",
                organization=organization,
                parent=parent,
                created_by=user
            )
            dept.full_clean()
        assert "Department hierarchy cannot exceed 5 levels" in str(exc_info.value)

    def test_team_inactive_department(self, department, user):
        """Test that teams cannot be created for inactive departments"""
        department.is_active = False
        department.save()
        with pytest.raises(ValidationError) as exc_info:
            Team.objects.create(
                name="Test Team",
                department=department,
                created_by=user
            )
        assert "Cannot create team for inactive department" in str(exc_info.value)

    def test_team_unique_name_in_department(self, department, user):
        """Test that team names must be unique within a department"""
        Team.objects.create(
            name="Test Team",
            department=department,
            created_by=user
        )
        with pytest.raises(ValidationError) as exc_info:
            Team.objects.create(
                name="Test Team",
                department=department,
                created_by=user
            )
        assert "A team with this name already exists in this department" in str(exc_info.value)

    def test_team_cross_department_parent(self, department, user):
        """Test that teams cannot have parents from different departments"""
        parent_team = Team.objects.create(
            name="Parent Team",
            department=department,
            created_by=user
        )
        other_dept = Department.objects.create(
            name="Other Dept",
            organization=department.organization,
            created_by=user
        )
        child_team = Team.objects.create(
            name="Child Team",
            department=other_dept,
            created_by=user
        )
        with pytest.raises(ValidationError) as exc_info:
            child_team.parent = parent_team
            child_team.save()
        assert "Parent team must belong to the same department" in str(exc_info.value)

    def test_team_self_parent(self, department, user):
        """Test that teams cannot be their own parent"""
        team = Team.objects.create(
            name="Test Team",
            department=department,
            created_by=user
        )
        with pytest.raises(ValidationError) as exc_info:
            team.parent = team
            team.save()
        assert "Team cannot be its own parent" in str(exc_info.value)

    def test_team_circular_reference(self, department, user):
        """Test that teams cannot create circular references"""
        team1 = Team.objects.create(
            name="Team 1",
            department=department,
            created_by=user
        )
        team2 = Team.objects.create(
            name="Team 2",
            department=department,
            parent=team1,
            created_by=user
        )
        team3 = Team.objects.create(
            name="Team 3",
            department=department,
            parent=team2,
            created_by=user
        )
        
        with pytest.raises(ValidationError) as exc_info:
            team1.parent = team3
            team1.save()
        assert "Circular reference detected in team hierarchy" in str(exc_info.value)

    def test_team_max_hierarchy_depth(self, department, user):
        """Test that teams cannot exceed maximum hierarchy depth"""
        # Create a hierarchy of 3 teams which is allowed by the model (depth < 3)
        team1 = Team.objects.create(
            name="Team 1",
            department=department,
            created_by=user
        )
        team2 = Team.objects.create(
            name="Team 2",
            department=department,
            parent=team1,
            created_by=user
        )
        team3 = Team.objects.create(
            name="Team 3",
            department=department,
            parent=team2,
            created_by=user
        )
        
        # Adding a 4th team should fail (depth >= 3)
        team4 = Team(
            name="Team 4",
            department=department,
            parent=team3,
            created_by=user
        )
        with pytest.raises(ValidationError) as exc_info:
            team4.full_clean()
        assert "Maximum team hierarchy depth exceeded" in str(exc_info.value)

    def test_team_member_inactive_team(self, team, user):
        """Test that team members cannot be added to inactive teams"""
        team.is_active = False
        team.save()
        with pytest.raises(ValidationError) as exc_info:
            TeamMember.objects.create(
                team=team,
                user=user,
                created_by=user
            )
        assert "Cannot add members to an inactive team" in str(exc_info.value)

    def test_team_member_unique_user(self, team, user):
        """Test that users cannot be added to the same team multiple times"""
        TeamMember.objects.create(
            team=team,
            user=user,
            created_by=user
        )
        with pytest.raises(ValidationError) as exc_info:
            TeamMember.objects.create(
                team=team,
                user=user,
                created_by=user
            )
        assert "This user is already a member of this team" in str(exc_info.value)

    def test_department_name_length(self, organization, user):
        """Test that department names cannot exceed maximum length"""
        with pytest.raises(ValidationError) as exc_info:
            Department.objects.create(
                name="A" * 101,  # Assuming max length is 100
                organization=organization,
                created_by=user
            )
        assert "Ensure this value has at most 100 characters" in str(exc_info.value)

    def test_department_update_operations(self, organization, user):
        """Test various department update operations"""
        dept1 = Department.objects.create(
            name="Test Dept 1",
            organization=organization,
            created_by=user
        )
        dept2 = Department.objects.create(
            name="Test Dept 2",
            organization=organization,
            created_by=user
        )
        
        # Test updating name to existing name
        with pytest.raises(ValidationError) as exc_info:
            dept2.name = "Test Dept 1"
            dept2.save()
        assert "A department with this name already exists in this organization" in str(exc_info.value)
        
        # Test updating to inactive organization
        dept1.organization.is_active = False
        dept1.organization.save()
        with pytest.raises(ValidationError) as exc_info:
            dept1.save()
        assert "Cannot create department for inactive organization" in str(exc_info.value)

    def test_organization_name_max_length(self):
        """Test organization name maximum length constraint"""
        with pytest.raises(ValidationError) as exc_info:
            Organization.objects.create(name="A" * 101)  # Assuming max length is 100
        assert "Ensure this value has at most 100 characters" in str(exc_info.value) 