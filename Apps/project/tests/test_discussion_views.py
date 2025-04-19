import pytest
import json
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from Apps.project.models import Project, ProjectDiscussion
from Apps.users.models import User
from .factories import ProjectFactory

pytestmark = pytest.mark.django_db

class TestProjectDiscussionAPI:
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def project(self):
        return ProjectFactory()
    
    @pytest.fixture
    def discussion(self, project):
        return ProjectDiscussion.objects.create(
            project=project,
            title="Test Discussion",
            content="This is a test discussion content",
            created_by=project.owner,
            updated_by=project.owner
        )
    
    def test_list_discussions(self, api_client, project, discussion):
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        # Create another discussion
        discussion2 = ProjectDiscussion.objects.create(
            project=project,
            title="Test Discussion 2",
            content="This is another test discussion",
            created_by=project.owner,
            updated_by=project.owner
        )
        
        url = reverse('project:project-discussions-list', kwargs={'project_pk': project.pk})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0]['title'] == discussion2.title
        assert response.data[1]['title'] == discussion.title
    
    def test_create_discussion(self, api_client, project):
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        url = reverse('project:project-discussions-list', kwargs={'project_pk': project.pk})
        data = {
            'title': 'New Discussion',
            'content': 'Content for the new discussion'
        }
        
        response = api_client.post(url, data=data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert ProjectDiscussion.objects.count() == 1
        assert response.data['title'] == 'New Discussion'
        assert response.data['content'] == 'Content for the new discussion'
    
    def test_create_discussion_with_invalid_data(self, api_client, project):
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        url = reverse('project:project-discussions-list', kwargs={'project_pk': project.pk})
        data = {
            'title': '',  # Invalid: title is required
            'content': 'Content for the new discussion'
        }
        
        response = api_client.post(url, data=data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_retrieve_discussion(self, api_client, project, discussion):
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        url = reverse('project:project-discussions-detail', kwargs={
            'project_pk': project.pk,
            'pk': discussion.pk
        })
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == discussion.title
        assert response.data['content'] == discussion.content
    
    def test_update_discussion(self, api_client, project, discussion):
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        url = reverse('project:project-discussions-detail', kwargs={
            'project_pk': project.pk,
            'pk': discussion.pk
        })
        
        data = {
            'title': 'Updated Discussion Title',
            'content': 'Updated content'
        }
        
        # Print details for debugging
        print(f"Project ID: {project.pk}")
        print(f"Discussion ID: {discussion.pk}")
        print(f"URL: {url}")
        print(f"Data: {data}")
        
        response = api_client.put(url, data=data, format='json')
        
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
        
        assert response.status_code == status.HTTP_200_OK
        
        # Refresh from database
        discussion.refresh_from_db()
        assert discussion.title == 'Updated Discussion Title'
        assert discussion.content == 'Updated content'
    
    def test_partial_update_discussion(self, api_client, project, discussion):
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        url = reverse('project:project-discussions-detail', kwargs={
            'project_pk': project.pk,
            'pk': discussion.pk
        })
        
        data = {
            'title': 'Partially Updated Title'
        }
        
        response = api_client.patch(url, data=data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Refresh from database
        discussion.refresh_from_db()
        assert discussion.title == 'Partially Updated Title'
        assert discussion.content == 'This is a test discussion content'  # Unchanged
    
    def test_delete_discussion(self, api_client, project, discussion):
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        url = reverse('project:project-discussions-detail', kwargs={
            'project_pk': project.pk,
            'pk': discussion.pk
        })
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify logical deletion
        discussion.refresh_from_db()
        assert discussion.is_active is False
    
    def test_unauthorized_access(self, api_client, project, discussion):
        # Create a user who is not part of the project
        unauthorized_user = ProjectFactory().owner
        api_client.force_authenticate(user=unauthorized_user)
        
        url = reverse('project:project-discussions-list', kwargs={'project_pk': project.pk})
        response = api_client.get(url)
        
        # Should be forbidden since user is not a project member
        assert response.status_code == status.HTTP_403_FORBIDDEN 