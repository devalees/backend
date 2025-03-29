import pytest
from django.urls import reverse, get_resolver
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from ..models import Project, Task
from .factories import ProjectFactory, TaskFactory
from Apps.users.tests.factories import UserFactory
from Apps.entity.tests.factories import OrganizationFactory, DepartmentFactory, TeamFactory, TeamMemberFactory
import logging

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(api_client):
    user = UserFactory()
    api_client.force_authenticate(user=user)
    return api_client, user

@pytest.fixture
def user_in_organization(authenticated_client):
    client, user = authenticated_client
    org = OrganizationFactory()
    dept = DepartmentFactory(organization=org)
    team = TeamFactory(department=dept)
    TeamMemberFactory(team=team, user=user)
    return client, user, org

def test_urls():
    """Test to print out all registered URLs"""
    from django.urls import get_resolver, reverse
    resolver = get_resolver()
    print("\nRegistered URLs:")
    for pattern in resolver.url_patterns:
        print(f"Pattern: {pattern.pattern}")
        if hasattr(pattern, 'url_patterns'):
            for subpattern in pattern.url_patterns:
                print(f"  Subpattern: {subpattern.pattern}")
                if hasattr(subpattern, 'url_patterns'):
                    for subsubpattern in subpattern.url_patterns:
                        print(f"    Subsubpattern: {subsubpattern.pattern}")
                        if hasattr(subsubpattern, 'lookup_str'):
                            print(f"      View: {subsubpattern.lookup_str}")
                        if hasattr(subsubpattern, 'name'):
                            print(f"      Name: {subsubpattern.name}")
                            try:
                                url = reverse(subsubpattern.name)
                                print(f"      URL: {url}")
                            except:
                                pass
                if hasattr(subpattern, 'lookup_str'):
                    print(f"    View: {subpattern.lookup_str}")
                if hasattr(subpattern, 'name'):
                    print(f"    Name: {subpattern.name}")
                    try:
                        url = reverse(subpattern.name)
                        print(f"    URL: {url}")
                    except:
                        pass
        if hasattr(pattern, 'lookup_str'):
            print(f"  View: {pattern.lookup_str}")
        if hasattr(pattern, 'name'):
            print(f"  Name: {pattern.name}")
            try:
                url = reverse(pattern.name)
                print(f"  URL: {url}")
            except:
                pass

    print("\nTesting project URLs:")
    try:
        url = reverse('project:project-list')
        print(f"project:project-list -> {url}")
    except Exception as e:
        print(f"Error getting project:project-list URL: {e}")

class TestProjectViewSet:
    def test_list_projects(self, user_in_organization):
        client, user, org = user_in_organization
        
        # Create projects
        project1 = ProjectFactory(organization=org, owner=user)
        project2 = ProjectFactory(organization=org)
        project2.team_members.add(user)
        ProjectFactory()  # Project user shouldn't see
        
        url = reverse('project:project-list')
        logger.info(f"Using URL: {url}")
        response = client.get(url)
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response content: {response.content}")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_create_project(self, user_in_organization):
        client, user, org = user_in_organization
        
        url = reverse('project:project-list')
        logger.info(f"Using URL: {url}")
        data = {
            'title': 'Test Project',
            'description': 'Test Description',
            'start_date': timezone.now().isoformat(),
            'end_date': (timezone.now() + timezone.timedelta(days=30)).isoformat(),
            'status': 'new',
            'priority': 'medium',
            'organization_id': org.id,
            'owner_id': user.id,
        }
        
        response = client.post(url, data, format='json')
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response content: {response.content}")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == data['title']
        assert response.data['owner']['id'] == user.id
        assert response.data['created_by']['id'] == user.id

    def test_add_team_members(self, user_in_organization):
        client, user, org = user_in_organization
        project = ProjectFactory(owner=user, organization=org)
        new_members = [UserFactory() for _ in range(2)]
        
        # Add new members to organization
        dept = DepartmentFactory(organization=org)
        team = TeamFactory(department=dept)
        for member in new_members:
            TeamMemberFactory(team=team, user=member)
        
        url = reverse('project:project-add-team-members', kwargs={'pk': project.id})
        data = {'user_ids': [member.id for member in new_members]}
        
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert all(member.id in [m['id'] for m in response.data['team_members']] 
                  for member in new_members)

class TestTaskViewSet:
    def test_list_tasks(self, user_in_organization):
        client, user, org = user_in_organization
        project = ProjectFactory(owner=user, organization=org)
        
        # Create tasks
        task1 = TaskFactory(project=project, assigned_to=user)
        task2 = TaskFactory(project=project)
        TaskFactory()  # Task user shouldn't see
        
        url = reverse('project:task-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_create_task(self, user_in_organization):
        client, user, org = user_in_organization
        project = ProjectFactory(owner=user, organization=org)
        
        url = reverse('project:task-list')
        data = {
            'title': 'Test Task',
            'description': 'Test Description',
            'due_date': timezone.now().isoformat(),
            'status': 'todo',
            'priority': 'medium',
            'project': project.id,
            'assigned_to_id': user.id,
        }
        
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == data['title']
        assert response.data['assigned_to']['id'] == user.id
        assert response.data['created_by']['id'] == user.id

    def test_assign_task(self, user_in_organization):
        client, user, org = user_in_organization
        project = ProjectFactory(owner=user, organization=org)
        task = TaskFactory(project=project)
        
        # Create new assignee in organization
        new_assignee = UserFactory()
        dept = DepartmentFactory(organization=org)
        team = TeamFactory(department=dept)
        TeamMemberFactory(team=team, user=new_assignee)
        
        url = reverse('project:task-assign', kwargs={'pk': task.id})
        data = {'user_id': new_assignee.id}
        
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['assigned_to']['id'] == new_assignee.id

    def test_change_task_status(self, user_in_organization):
        client, user, org = user_in_organization
        project = ProjectFactory(owner=user, organization=org)
        task = TaskFactory(project=project, status=Task.Status.TODO)
        
        url = reverse('project:task-change-status', kwargs={'pk': task.id})
        data = {'status': Task.Status.IN_PROGRESS}
        
        response = client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == Task.Status.IN_PROGRESS
