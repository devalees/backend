import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from Apps.project.models import Project, Task, ProjectPhase, Milestone, ProjectSchedule
from Apps.time_management.models import TimeEntry, TimeCategory
from Apps.users.models import User
from Apps.entity.models import Organization, Department, Team, TeamMember

@pytest.fixture
@pytest.mark.django_db
def organization():
    return Organization.objects.create(name="Test Organization")

@pytest.fixture
@pytest.mark.django_db
def user():
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpassword"
    )

@pytest.fixture
@pytest.mark.django_db
def department(organization):
    return Department.objects.create(
        name="Test Department",
        organization=organization
    )

@pytest.fixture
@pytest.mark.django_db
def team(department):
    return Team.objects.create(
        name="Test Team",
        department=department
    )

@pytest.fixture
@pytest.mark.django_db
def team_member(user, team):
    return TeamMember.objects.create(
        user=user,
        team=team,
        role="member"
    )

@pytest.fixture
@pytest.mark.django_db
def project(organization, user, team_member):
    project = Project.objects.create(
        title="Test Project",
        description="Test Description",
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=30),
        status=Project.Status.NEW,
        priority=Project.Priority.MEDIUM,
        owner=user,
        organization=organization
    )
    project.team_members.add(user)
    return project

@pytest.fixture
@pytest.mark.django_db
def task(project, user):
    return Task.objects.create(
        title="Test Task",
        description="Test task description",
        due_date=timezone.now() + timedelta(days=7),
        status=Task.Status.TODO,
        priority=Task.Priority.MEDIUM,
        project=project,
        assigned_to=user,
        estimated_hours=Decimal("10.0")
    )

@pytest.fixture
@pytest.mark.django_db
def project_schedule(project):
    return ProjectSchedule.objects.create(
        project=project,
        estimated_start_date=project.start_date,
        estimated_end_date=project.end_date,
        description="Test Schedule",
        estimated_hours=Decimal("100.0")
    )

@pytest.fixture
@pytest.mark.django_db
def project_phase(project_schedule):
    return ProjectPhase.objects.create(
        name="Development Phase",
        description="Development activities",
        schedule=project_schedule,
        start_date=project_schedule.estimated_start_date,
        end_date=project_schedule.estimated_start_date + timedelta(days=15),
        order=1,
        estimated_hours=Decimal("50.0")
    )

@pytest.fixture
@pytest.mark.django_db
def milestone(project_schedule, project_phase):
    return Milestone.objects.create(
        name="Alpha Release",
        description="Alpha version release",
        schedule=project_schedule,
        phase=project_phase,
        due_date=project_schedule.estimated_start_date + timedelta(days=10),
        status='pending',
        estimated_hours=Decimal("25.0")
    )

@pytest.fixture
@pytest.mark.django_db
def time_category():
    return TimeCategory.objects.create(
        name="Development",
        description="Development work",
        color="#FF5733"
    )

@pytest.fixture
@pytest.mark.django_db
def time_entries(project, user, task, project_phase, milestone, time_category):
    entries = []
    
    # Create time entries for different days
    # Linked to task
    entries.append(TimeEntry.objects.create(
        user=user,
        project=project,
        task=task,
        category=time_category,
        description="Task development work",
        start_time=timezone.now() - timedelta(days=3, hours=2),
        end_time=timezone.now() - timedelta(days=3),
        hours=Decimal("2.0"),
        is_billable=True,
        created_by=user,
        updated_by=user
    ))
    
    # Linked to phase
    entries.append(TimeEntry.objects.create(
        user=user,
        project=project,
        project_phase=project_phase,
        category=time_category,
        description="Phase general work",
        start_time=timezone.now() - timedelta(days=2, hours=3),
        end_time=timezone.now() - timedelta(days=2),
        hours=Decimal("3.0"),
        is_billable=True,
        created_by=user,
        updated_by=user
    ))
    
    # Linked to milestone
    entries.append(TimeEntry.objects.create(
        user=user,
        project=project,
        milestone=milestone,
        category=time_category,
        description="Milestone preparation",
        start_time=timezone.now() - timedelta(days=1, hours=4),
        end_time=timezone.now() - timedelta(days=1),
        hours=Decimal("4.0"),
        is_billable=False,
        created_by=user,
        updated_by=user
    ))
    
    return entries

@pytest.fixture
@pytest.mark.django_db
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
class TestProjectTimeEntries:
    """Tests for project time entries endpoints"""
    
    def test_list_project_time_entries(self, api_client, project, time_entries):
        """Test retrieving all time entries for a project"""
        url = reverse('project:project-time-entries', args=[project.id])
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3  # We created 3 time entries for this project
        # Verify the first entry has the correct structure
        assert 'id' in response.data[0]
        assert 'user' in response.data[0]
        assert 'project' in response.data[0]
        assert 'hours' in response.data[0]
        assert 'is_billable' in response.data[0]
    
    def test_project_time_entries_filter_by_task(self, api_client, project, task, time_entries):
        """Test filtering time entries by task"""
        url = f"{reverse('project:project-time-entries', args=[project.id])}?task_id={task.id}"
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # Only one entry linked to the task
        assert response.data[0]['task'] == task.id
    
    def test_project_time_entries_filter_by_phase(self, api_client, project, project_phase, time_entries):
        """Test filtering time entries by phase"""
        url = f"{reverse('project:project-time-entries', args=[project.id])}?phase_id={project_phase.id}"
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # Only one entry linked to the phase
        assert response.data[0]['project_phase'] == project_phase.id
    
    def test_project_time_entries_filter_by_milestone(self, api_client, project, milestone, time_entries):
        """Test filtering time entries by milestone"""
        url = f"{reverse('project:project-time-entries', args=[project.id])}?milestone_id={milestone.id}"
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # Only one entry linked to the milestone
        assert response.data[0]['milestone'] == milestone.id
    
    def test_project_time_entries_filter_by_billable(self, api_client, project, time_entries):
        """Test filtering time entries by billable status"""
        url = f"{reverse('project:project-time-entries', args=[project.id])}?is_billable=true"
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # Two entries are billable
        assert all(entry['is_billable'] for entry in response.data)

@pytest.mark.django_db
class TestProjectTimeReport:
    """Tests for project time report endpoint"""
    
    def test_project_time_report(self, api_client, project, time_entries):
        """Test retrieving time report for a project"""
        url = reverse('project:project-time-report', args=[project.id])
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Check report structure
        assert 'total_entries' in response.data
        assert 'total_hours' in response.data
        assert 'by_user' in response.data
        assert 'by_task' in response.data
        assert 'timeline_daily' in response.data
        assert 'billable_hours' in response.data
        assert 'non_billable_hours' in response.data
        
        # Verify the values
        assert response.data['total_entries'] == 3
        assert float(response.data['total_hours']) == 9.0  # Sum of 2.0 + 3.0 + 4.0
        assert float(response.data['billable_hours']) == 5.0  # Sum of 2.0 + 3.0
        assert float(response.data['non_billable_hours']) == 4.0
    
    def test_project_time_report_with_date_range(self, api_client, project, time_entries):
        """Test time report with date filters"""
        # Get data for just the last two days
        start_date = (timezone.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        url = f"{reverse('project:project-time-report', args=[project.id])}?start_date={start_date}"
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_entries'] == 2  # Entries from the last 2 days
        assert float(response.data['total_hours']) == 7.0  # Hours from day -1 (4.0) + day -2 (3.0) entries

@pytest.mark.django_db
class TestProjectBurndownChart:
    """Tests for project burndown chart endpoint"""
    
    def test_project_burndown_chart(self, api_client, project, project_schedule, time_entries):
        """Test retrieving burndown chart data for a project"""
        url = reverse('project:project-burndown', args=[project.id])
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) > 0
        
        # Verify the first point structure (initial point)
        assert 'date' in response.data[0]
        assert 'remaining' in response.data[0]
        
        # Verify the last point shows less remaining work than the first
        assert float(response.data[0]['remaining']) > float(response.data[-1]['remaining'])

@pytest.mark.django_db
class TestTaskTimeEntries:
    """Tests for task time entries endpoints"""
    
    def test_list_task_time_entries(self, api_client, project, task, time_entries):
        """Test retrieving all time entries for a specific task"""
        url = reverse('project:task-time-entries', args=[task.id])
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # Only one entry for this task
        assert response.data[0]['task'] == task.id

@pytest.mark.django_db
class TestPhaseTimeEntries:
    """Tests for phase time entries endpoints"""
    
    def test_list_phase_time_entries(self, api_client, project_phase, time_entries):
        """Test retrieving all time entries for a specific phase"""
        url = reverse('project:phase-time-entries', args=[project_phase.id])
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # Only one entry for this phase
        assert response.data[0]['project_phase'] == project_phase.id

@pytest.mark.django_db
class TestMilestoneTimeEntries:
    """Tests for milestone time entries endpoints"""
    
    def test_list_milestone_time_entries(self, api_client, milestone, time_entries):
        """Test retrieving all time entries for a specific milestone"""
        url = reverse('project:milestone-time-entries', args=[milestone.id])
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # Only one entry for this milestone
        assert response.data[0]['milestone'] == milestone.id

@pytest.mark.django_db
class TestProjectTimeDashboard:
    """Tests for project time dashboard endpoint"""
    
    def test_project_time_dashboard(self, api_client, project, time_entries):
        """Test retrieving time dashboard data for a project"""
        url = reverse('project:project-time-dashboard', args=[project.id])
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Verify dashboard structure
        assert 'total_hours' in response.data
        assert 'estimated_hours' in response.data
        assert 'variance_hours' in response.data
        assert 'variance_percentage' in response.data
        assert 'by_task' in response.data
        assert 'by_phase' in response.data
        assert 'by_milestone' in response.data
        assert 'by_user' in response.data
        assert 'by_date' in response.data 