import pytest
import json
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from Apps.project.models import ProjectDiscussion
from .factories import ProjectFactory

pytestmark = pytest.mark.django_db

class TestDiscussionCaching:
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
    
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        """Clear the cache before each test"""
        cache.clear()
        yield
        cache.clear()
    
    def test_get_discussions_with_cache(self, api_client, project, discussion):
        """Test that discussions are cached when retrieved"""
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        url = reverse('project:project-discussions-list', kwargs={'project_pk': project.pk})
        cache_key = f'project_discussions_{project.pk}'
        
        # First call to fill the cache
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        
        # Verify cache was set
        cached_data = cache.get(cache_key)
        assert cached_data is not None
        assert len(json.loads(cached_data)) == 1
        
        # Create a new discussion without invalidating cache
        ProjectDiscussion.objects.create(
            project=project,
            title="Test Discussion 2",
            content="This is another test discussion",
            created_by=project.owner,
            updated_by=project.owner
        )
        
        # Get discussions again with a patch to track database access
        # Note: We need to ignore the pk__in filter call which is used to fetch from cache
        with patch('Apps.project.models.ProjectDiscussion.objects.filter', wraps=ProjectDiscussion.objects.filter) as mock_filter:
            response = api_client.get(url)
            
            # Verify database was not queried (except for the pk__in filter to load from cache)
            # The filter should be called only with pk__in from the cached data
            db_queries = [call for call in mock_filter.call_args_list if not (len(call[0]) == 0 and 'pk__in' in call[1])]
            assert len(db_queries) == 0
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1  # Still showing 1 from cache
        
        # Get with cache-busting parameter
        response = api_client.get(f"{url}?refresh=true")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # Now showing both discussions
        
        # Verify cache was updated
        cached_data = cache.get(cache_key)
        assert cached_data is not None
        assert len(json.loads(cached_data)) == 2
    
    def test_cache_invalidation_on_update(self, api_client, project, discussion):
        """Test that cache is invalidated when a discussion is updated"""
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        cache_key = f'project_discussions_{project.pk}'
        
        # Get discussions to populate cache
        url = reverse('project:project-discussions-list', kwargs={'project_pk': project.pk})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify cache was set
        assert cache.get(cache_key) is not None
        
        # Update discussion
        update_url = reverse('project:project-discussions-detail', kwargs={
            'project_pk': project.pk,
            'pk': discussion.pk
        })
        
        data = {
            'title': 'Updated Discussion Title',
            'content': 'Updated content'
        }
        
        response = api_client.put(update_url, data=data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Verify cache was invalidated
        assert cache.get(cache_key) is None
    
    def test_cache_invalidation_on_create(self, api_client, project):
        """Test that cache is invalidated when a new discussion is created"""
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        cache_key = f'project_discussions_{project.pk}'
        
        # Manually set cache
        cache.set(cache_key, json.dumps([]), 3600)
        
        # Verify cache is set
        assert cache.get(cache_key) is not None
        
        # Create discussion
        url = reverse('project:project-discussions-list', kwargs={'project_pk': project.pk})
        data = {
            'title': 'New Discussion',
            'content': 'Content for the new discussion'
        }
        
        response = api_client.post(url, data=data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify cache was invalidated
        assert cache.get(cache_key) is None
    
    def test_cache_invalidation_on_delete(self, api_client, project, discussion):
        """Test that cache is invalidated when a discussion is deleted"""
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        cache_key = f'project_discussions_{project.pk}'
        
        # Get discussions to populate cache
        url = reverse('project:project-discussions-list', kwargs={'project_pk': project.pk})
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify cache was set
        assert cache.get(cache_key) is not None
        
        # Delete discussion
        delete_url = reverse('project:project-discussions-detail', kwargs={
            'project_pk': project.pk,
            'pk': discussion.pk
        })
        
        response = api_client.delete(delete_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify cache was invalidated
        assert cache.get(cache_key) is None 