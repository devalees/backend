import pytest
import tempfile
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from Apps.project.models import Project, ProjectDiscussion, DiscussionAttachment
from .factories import ProjectFactory

pytestmark = pytest.mark.django_db

class TestDiscussionAttachments:
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
    
    @pytest.fixture
    def temp_file(self):
        with tempfile.NamedTemporaryFile(suffix='.txt') as temp:
            temp.write(b'Test file content')
            temp.flush()
            temp.seek(0)
            yield temp
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_create_attachment(self, api_client, project, discussion, temp_file):
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        # Create file for attachment
        uploaded_file = SimpleUploadedFile(
            name='test_file.txt',
            content=b'Test file content',
            content_type='text/plain'
        )
        
        url = reverse('project:discussion-attachments-list', kwargs={
            'project_pk': project.pk,
            'discussion_pk': discussion.pk
        })
        
        data = {
            'file': uploaded_file,
            'description': 'Test attachment description'
        }
        
        response = api_client.post(url, data=data, format='multipart')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert DiscussionAttachment.objects.count() == 1
        assert response.data['description'] == 'Test attachment description'
        assert 'file' in response.data
        assert 'filename' in response.data
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_list_attachments(self, api_client, project, discussion, temp_file):
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        # Create attachment
        file = SimpleUploadedFile(
            name='test_file.txt',
            content=b'Test file content',
            content_type='text/plain'
        )
        
        attachment = DiscussionAttachment.objects.create(
            discussion=discussion,
            file=file,
            description='Test attachment',
            created_by=project.owner,
            updated_by=project.owner
        )
        
        # Create another attachment
        file2 = SimpleUploadedFile(
            name='test_file2.txt',
            content=b'Test file content 2',
            content_type='text/plain'
        )
        
        attachment2 = DiscussionAttachment.objects.create(
            discussion=discussion,
            file=file2,
            description='Test attachment 2',
            created_by=project.owner,
            updated_by=project.owner
        )
        
        url = reverse('project:discussion-attachments-list', kwargs={
            'project_pk': project.pk,
            'discussion_pk': discussion.pk
        })
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_retrieve_attachment(self, api_client, project, discussion, temp_file):
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        # Create attachment
        file = SimpleUploadedFile(
            name='test_file.txt',
            content=b'Test file content',
            content_type='text/plain'
        )
        
        attachment = DiscussionAttachment.objects.create(
            discussion=discussion,
            file=file,
            description='Test attachment',
            created_by=project.owner,
            updated_by=project.owner
        )
        
        url = reverse('project:discussion-attachments-detail', kwargs={
            'project_pk': project.pk,
            'discussion_pk': discussion.pk,
            'pk': attachment.pk
        })
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == 'Test attachment'
    
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_delete_attachment(self, api_client, project, discussion, temp_file):
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        # Create attachment
        file = SimpleUploadedFile(
            name='test_file.txt',
            content=b'Test file content',
            content_type='text/plain'
        )
        
        attachment = DiscussionAttachment.objects.create(
            discussion=discussion,
            file=file,
            description='Test attachment',
            created_by=project.owner,
            updated_by=project.owner
        )
        
        url = reverse('project:discussion-attachments-detail', kwargs={
            'project_pk': project.pk,
            'discussion_pk': discussion.pk,
            'pk': attachment.pk
        })
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert DiscussionAttachment.objects.filter(pk=attachment.pk).exists() is False 