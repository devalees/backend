import pytest
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from Apps.project.models import Project, ProjectSchedule, ProjectPhase, Milestone
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
def project_schedule(project):
    return ProjectSchedule.objects.create(
        project=project,
        estimated_start_date=project.start_date,
        estimated_end_date=project.end_date,
        description="Test Schedule"
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
        order=1
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
        status='pending'
    )

@pytest.fixture
@pytest.mark.django_db
def api_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
class TestProjectScheduleModel:
    """Tests for the ProjectSchedule model"""
    
    def test_create_project_schedule(self, project):
        """Test creating a project schedule"""
        schedule = ProjectSchedule(
            project=project,
            estimated_start_date=project.start_date,
            estimated_end_date=project.end_date,
            description="Test Schedule"
        )
        schedule.save()
        
        assert schedule.pk is not None
        assert schedule.project == project
        assert schedule.estimated_start_date == project.start_date
        assert schedule.estimated_end_date == project.end_date
    
    def test_project_schedule_str(self, project_schedule):
        """Test string representation of project schedule"""
        assert str(project_schedule) == f"Schedule for {project_schedule.project.title}"
    
    def test_date_validation(self, project):
        """Test start date must be before end date"""
        schedule = ProjectSchedule(
            project=project,
            estimated_start_date=project.start_date + timedelta(days=10),
            estimated_end_date=project.start_date,
            description="Invalid Schedule"
        )
        
        with pytest.raises(ValidationError) as excinfo:
            schedule.full_clean()
        
        errors = excinfo.value.error_dict
        assert '__all__' in errors
        assert 'Estimated start date must be before estimated end date' in str(errors['__all__'])
    
    def test_project_relation(self, project_schedule, project):
        """Test relationship with project model"""
        assert project_schedule.project == project
        assert hasattr(project, 'schedule')
        assert project.schedule == project_schedule

@pytest.mark.django_db
class TestProjectPhaseModel:
    """Tests for the ProjectPhase model"""
    
    def test_create_project_phase(self, project_schedule):
        """Test creating a project phase"""
        phase = ProjectPhase(
            name="Testing Phase",
            description="Testing activities",
            schedule=project_schedule,
            start_date=project_schedule.estimated_start_date + timedelta(days=15),
            end_date=project_schedule.estimated_end_date,
            order=2
        )
        phase.save()
        
        assert phase.pk is not None
        assert phase.schedule == project_schedule
        assert phase.name == "Testing Phase"
    
    def test_phase_str(self, project_phase):
        """Test string representation of project phase"""
        assert str(project_phase) == project_phase.name
    
    def test_date_validation(self, project_schedule):
        """Test start date must be before end date"""
        phase = ProjectPhase(
            name="Invalid Phase",
            description="Invalid phase",
            schedule=project_schedule,
            start_date=project_schedule.estimated_start_date + timedelta(days=20),
            end_date=project_schedule.estimated_start_date + timedelta(days=10),
            order=3
        )
        
        with pytest.raises(ValidationError) as excinfo:
            phase.full_clean()
        
        errors = excinfo.value.error_dict
        assert '__all__' in errors
        assert 'Start date must be before end date' in str(errors['__all__'])
    
    def test_schedule_date_boundaries(self, project_schedule):
        """Test phase dates must be within schedule boundaries"""
        phase = ProjectPhase(
            name="Out of Bounds Phase",
            description="Phase outside schedule dates",
            schedule=project_schedule,
            start_date=project_schedule.estimated_start_date - timedelta(days=5),
            end_date=project_schedule.estimated_end_date + timedelta(days=5),
            order=4
        )
        
        with pytest.raises(ValidationError) as excinfo:
            phase.full_clean()
        
        errors = excinfo.value.error_dict
        assert '__all__' in errors
        assert 'Phase start date cannot be before schedule start date' in str(errors['__all__']) or \
               'Phase end date cannot be after schedule end date' in str(errors['__all__'])

@pytest.mark.django_db
class TestMilestoneModel:
    """Tests for the Milestone model"""
    
    def test_create_milestone(self, project_schedule, project_phase):
        """Test creating a milestone"""
        milestone = Milestone(
            name="Beta Release",
            description="Beta version release",
            schedule=project_schedule,
            phase=project_phase,
            due_date=project_phase.end_date - timedelta(days=1),  # Ensure due date is before phase end date
            status='pending'
        )
        milestone.save()
        
        assert milestone.pk is not None
        assert milestone.schedule == project_schedule
        assert milestone.phase == project_phase
        assert milestone.name == "Beta Release"
    
    def test_milestone_str(self, milestone):
        """Test string representation of milestone"""
        assert str(milestone) == milestone.name
    
    def test_due_date_validation(self, project_schedule, project_phase):
        """Test due date must be within schedule boundaries"""
        milestone = Milestone(
            name="Invalid Milestone",
            description="Milestone with invalid due date",
            schedule=project_schedule,
            phase=project_phase,
            due_date=project_schedule.estimated_end_date + timedelta(days=10),
            status='pending'
        )
        
        with pytest.raises(ValidationError) as excinfo:
            milestone.full_clean()
        
        errors = excinfo.value.error_dict
        assert '__all__' in errors
        assert 'Milestone due date cannot be after schedule end date' in str(errors['__all__'])
    
    def test_status_validation(self, project_schedule, project_phase):
        """Test milestone status validation"""
        milestone = Milestone(
            name="Invalid Status Milestone",
            description="Milestone with invalid status",
            schedule=project_schedule,
            phase=project_phase,
            due_date=project_schedule.estimated_start_date + timedelta(days=15),
            status='invalid_status'
        )
        
        with pytest.raises(ValidationError) as excinfo:
            milestone.full_clean()
        
        assert "status" in str(excinfo.value)

@pytest.mark.django_db
class TestProjectScheduleAPI:
    """Tests for the ProjectSchedule API endpoints"""
    
    def test_create_schedule(self, api_client, project):
        """Test creating a schedule via API"""
        url = reverse('project:projectschedule-list')
        data = {
            'project': project.id,
            'estimated_start_date': project.start_date.isoformat(),
            'estimated_end_date': project.end_date.isoformat(),
            'description': 'API Test Schedule'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['project'] == project.id
        assert response.data['description'] == 'API Test Schedule'
    
    def test_get_schedule_list(self, api_client, project_schedule):
        """Test getting list of schedules"""
        url = reverse('project:projectschedule-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_get_schedule_detail(self, api_client, project_schedule):
        """Test getting schedule detail"""
        url = reverse('project:projectschedule-detail', args=[project_schedule.id])
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == project_schedule.id
        assert response.data['project'] == project_schedule.project.id
    
    def test_update_schedule(self, api_client, project_schedule):
        """Test updating a schedule"""
        url = reverse('project:projectschedule-detail', args=[project_schedule.id])
        data = {
            'project': project_schedule.project.id,
            'estimated_start_date': project_schedule.estimated_start_date.isoformat(),
            'estimated_end_date': project_schedule.estimated_end_date.isoformat(),
            'description': 'Updated Schedule Description'
        }
        
        response = api_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == 'Updated Schedule Description'
    
    def test_delete_schedule(self, api_client, project_schedule):
        """Test deleting a schedule"""
        url = reverse('project:projectschedule-detail', args=[project_schedule.id])
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert ProjectSchedule.objects.filter(id=project_schedule.id).count() == 0 