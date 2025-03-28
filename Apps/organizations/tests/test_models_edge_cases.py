import pytest
from django.core.exceptions import ValidationError
from Apps.organizations.models import Organization, Department, Team, TeamMember
from Apps.users.models import User

@pytest.mark.django_db
class TestOrganizationModelEdgeCases:
    @pytest.fixture
    def organization(self):
        return Organization.objects.create(name="Test Org")

    @pytest.fixture
    def department(self, organization):
        return Department.objects.create(name="Test Dept", organization=organization)

    @pytest.fixture
    def team(self, department):
        return Team.objects.create(name="Test Team", department=department)

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_organization_unique_name_validation(self):
        """Test that organization names must be unique"""
        Organization.objects.create(name="Test Org")
        with pytest.raises(ValidationError) as exc_info:
            Organization.objects.create(name="Test Org")
        assert "Organization with this Name already exists" in str(exc_info.value)

    def test_department_inactive_organization(self, organization):
        """Test that departments cannot be created for inactive organizations"""
        organization.is_active = False
        organization.save()
        with pytest.raises(ValidationError) as exc_info:
            Department.objects.create(name="Test Dept", organization=organization)
        assert "Cannot create department for inactive organization" in str(exc_info.value)

    def test_department_unique_name_in_organization(self, organization):
        """Test that department names must be unique within an organization"""
        Department.objects.create(name="Test Dept", organization=organization)
        with pytest.raises(ValidationError) as exc_info:
            Department.objects.create(name="Test Dept", organization=organization)
        assert "Department with this Name and Organization already exists" in str(exc_info.value)

    def test_department_cross_organization_parent(self, organization):
        """Test that departments cannot have parents from different organizations"""
        parent_dept = Department.objects.create(name="Parent Dept", organization=organization)
        other_org = Organization.objects.create(name="Other Org")
        child_dept = Department.objects.create(name="Child Dept", organization=other_org)
        with pytest.raises(ValidationError) as exc_info:
            child_dept.parent = parent_dept
            child_dept.save()
        assert "Parent department must belong to the same organization" in str(exc_info.value)

    def test_department_self_parent(self, organization):
        """Test that departments cannot be their own parent"""
        dept = Department.objects.create(name="Test Dept", organization=organization)
        with pytest.raises(ValidationError) as exc_info:
            dept.parent = dept
            dept.save()
        assert "Department cannot be its own parent" in str(exc_info.value)

    def test_department_circular_reference(self, organization):
        """Test that departments cannot create circular references"""
        dept1 = Department.objects.create(name="Dept 1", organization=organization)
        dept2 = Department.objects.create(name="Dept 2", organization=organization)
        dept3 = Department.objects.create(name="Dept 3", organization=organization)
        
        dept2.parent = dept1
        dept2.save()
        dept3.parent = dept2
        dept3.save()
        
        with pytest.raises(ValidationError) as exc_info:
            dept1.parent = dept3
            dept1.save()
        assert "Circular reference detected in department hierarchy" in str(exc_info.value)

    def test_department_max_hierarchy_depth(self, organization):
        """Test that departments cannot exceed maximum hierarchy depth"""
        parent = None
        for i in range(6):  # Assuming max depth is 5
            dept = Department.objects.create(
                name=f"Dept {i}",
                organization=organization,
                parent=parent
            )
            parent = dept
        
        with pytest.raises(ValidationError) as exc_info:
            Department.objects.create(
                name="Too Deep",
                organization=organization,
                parent=parent
            )
        assert "Maximum department hierarchy depth exceeded" in str(exc_info.value)

    def test_team_inactive_department(self, department):
        """Test that teams cannot be created for inactive departments"""
        department.is_active = False
        department.save()
        with pytest.raises(ValidationError) as exc_info:
            Team.objects.create(name="Test Team", department=department)
        assert "Cannot create team for inactive department" in str(exc_info.value)

    def test_team_unique_name_in_department(self, department):
        """Test that team names must be unique within a department"""
        Team.objects.create(name="Test Team", department=department)
        with pytest.raises(ValidationError) as exc_info:
            Team.objects.create(name="Test Team", department=department)
        assert "Team with this Name and Department already exists" in str(exc_info.value)

    def test_team_cross_department_parent(self, department):
        """Test that teams cannot have parents from different departments"""
        parent_team = Team.objects.create(name="Parent Team", department=department)
        other_dept = Department.objects.create(name="Other Dept", organization=department.organization)
        child_team = Team.objects.create(name="Child Team", department=other_dept)
        with pytest.raises(ValidationError) as exc_info:
            child_team.parent = parent_team
            child_team.save()
        assert "Parent team must belong to the same department" in str(exc_info.value)

    def test_team_self_parent(self, department):
        """Test that teams cannot be their own parent"""
        team = Team.objects.create(name="Test Team", department=department)
        with pytest.raises(ValidationError) as exc_info:
            team.parent = team
            team.save()
        assert "Team cannot be its own parent" in str(exc_info.value)

    def test_team_circular_reference(self, department):
        """Test that teams cannot create circular references"""
        team1 = Team.objects.create(name="Team 1", department=department)
        team2 = Team.objects.create(name="Team 2", department=department)
        team3 = Team.objects.create(name="Team 3", department=department)
        
        team2.parent = team1
        team2.save()
        team3.parent = team2
        team3.save()
        
        with pytest.raises(ValidationError) as exc_info:
            team1.parent = team3
            team1.save()
        assert "Circular reference detected in team hierarchy" in str(exc_info.value)

    def test_team_max_hierarchy_depth(self, department):
        """Test that teams cannot exceed maximum hierarchy depth"""
        parent = None
        for i in range(6):  # Assuming max depth is 5
            team = Team.objects.create(
                name=f"Team {i}",
                department=department,
                parent=parent
            )
            parent = team
        
        with pytest.raises(ValidationError) as exc_info:
            Team.objects.create(
                name="Too Deep",
                department=department,
                parent=parent
            )
        assert "Maximum team hierarchy depth exceeded" in str(exc_info.value)

    def test_team_member_inactive_team(self, team):
        """Test that team members cannot be added to inactive teams"""
        team.is_active = False
        team.save()
        with pytest.raises(ValidationError) as exc_info:
            TeamMember.objects.create(team=team, user=self.user)
        assert "Cannot add member to inactive team" in str(exc_info.value)

    def test_team_member_unique_user(self, team, user):
        """Test that users cannot be added to the same team multiple times"""
        TeamMember.objects.create(team=team, user=user)
        with pytest.raises(ValidationError) as exc_info:
            TeamMember.objects.create(team=team, user=user)
        assert "User is already a member of this team" in str(exc_info.value)

    def test_department_name_length(self, organization):
        """Test that department names cannot exceed maximum length"""
        with pytest.raises(ValidationError) as exc_info:
            Department.objects.create(
                name="A" * 101,  # Assuming max length is 100
                organization=organization
            )
        assert "Department name cannot exceed 100 characters" in str(exc_info.value)

    def test_department_update_operations(self, organization):
        """Test various department update operations"""
        dept = Department.objects.create(name="Test Dept", organization=organization)
        
        # Test updating name to existing name
        with pytest.raises(ValidationError) as exc_info:
            dept.name = "Test Dept"
            dept.save()
        assert "Department with this name already exists" in str(exc_info.value)
        
        # Test updating to inactive organization
        dept.organization.is_active = False
        dept.organization.save()
        with pytest.raises(ValidationError) as exc_info:
            dept.save()
        assert "Cannot update department for inactive organization" in str(exc_info.value) 