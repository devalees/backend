import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from Apps.organizations.models import Organization, Department, Team
from Apps.users.models import User

@pytest.mark.django_db
class TestTeamHierarchy:
    @pytest.fixture
    def organization(self):
        return Organization.objects.create(name='Test Org')

    @pytest.fixture
    def department(self, organization):
        return Department.objects.create(name='Engineering', organization=organization)

    @pytest.fixture
    def parent_team(self, department):
        return Team.objects.create(
            name='Frontend Team',
            department=department,
            description='Main Frontend Team'
        )

    def test_create_sub_team(self, parent_team, department):
        """Test creating a sub-team"""
        sub_team = Team.objects.create(
            name='UI Components Team',
            department=department,
            parent=parent_team,
            description='UI Components Sub-team'
        )
        assert sub_team.parent == parent_team
        assert sub_team in parent_team.sub_teams.all()
        assert str(sub_team) == 'UI Components Team'

    def test_team_hierarchy_depth(self, parent_team, department):
        """Test team hierarchy depth limit"""
        # Create first level sub-team (should succeed)
        sub_team1 = Team.objects.create(
            name='Level 1 Team',
            department=department,
            parent=parent_team
        )
        # Create second level sub-team (should succeed)
        sub_team2 = Team.objects.create(
            name='Level 2 Team',
            department=department,
            parent=sub_team1
        )
        # Try to create third level sub-team (should fail)
        team3 = Team(
            name='Level 3 Team',
            department=department,
            parent=sub_team2
        )
        with pytest.raises(ValidationError) as exc_info:
            team3.full_clean()
        assert "Maximum team hierarchy depth exceeded" in str(exc_info.value)

    def test_team_circular_reference(self, parent_team, department):
        """Test preventing circular references in team hierarchy"""
        sub_team = Team.objects.create(
            name='Sub Team',
            department=department,
            parent=parent_team
        )
        # Try to make parent team a child of its sub-team
        parent_team.parent = sub_team
        with pytest.raises(ValidationError):
            parent_team.full_clean()

    def test_team_department_consistency(self, parent_team, department):
        """Test that sub-teams must belong to the same department as parent"""
        other_department = Department.objects.create(
            name='Design',
            organization=parent_team.department.organization
        )
        team = Team(
            name='Invalid Team',
            department=other_department,
            parent=parent_team
        )
        with pytest.raises(ValidationError):
            team.full_clean()

    def test_team_hierarchy_representation(self, parent_team, department):
        """Test string representation of team hierarchy"""
        sub_team = Team.objects.create(
            name='Sub Team',
            department=department,
            parent=parent_team
        )
        assert str(sub_team) == 'Sub Team'
        assert sub_team.get_hierarchy_path() == 'Frontend Team > Sub Team'

    def test_team_hierarchy_queries(self, parent_team, department):
        """Test team hierarchy query methods"""
        sub_team1 = Team.objects.create(
            name='Sub Team 1',
            department=department,
            parent=parent_team
        )
        sub_team2 = Team.objects.create(
            name='Sub Team 2',
            department=department,
            parent=parent_team
        )
        # Test getting all sub-teams
        assert set(parent_team.sub_teams.all()) == {sub_team1, sub_team2}
        # Test getting all parent teams
        assert sub_team1.get_parent_teams() == [parent_team]
        # Test getting root team
        assert sub_team1.get_root_team() == parent_team

    def test_team_hierarchy_deletion(self, parent_team, department):
        """Test team hierarchy deletion behavior"""
        sub_team = Team.objects.create(
            name='Sub Team',
            department=department,
            parent=parent_team
        )
        # Delete parent team
        parent_team.delete()
        # Verify sub-team is also soft deleted
        sub_team.refresh_from_db()
        assert not sub_team.is_active 