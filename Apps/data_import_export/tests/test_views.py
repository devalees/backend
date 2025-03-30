import pytest
from django.urls import reverse, include, path
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient
import io
import csv
from ..models import ImportExportConfig, ImportExportLog
from .factories import (
    UserFactory,
    ContentTypeFactory,
    ImportExportConfigFactory,
    ImportExportLogFactory
)


@pytest.fixture
def api_client():
    """Fixture for API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    """Fixture for authenticated API client."""
    user = UserFactory()
    api_client.force_authenticate(user=user)
    return api_client, user


@pytest.fixture(autouse=True)
def setup_urls():
    """Fixture to set up URLs for testing."""
    from django.urls import clear_url_caches, set_urlconf
    from ..urls import urlpatterns
    
    # Create a temporary URLconf module
    temp_urlpatterns = [
        path('api/import-export/', include('Apps.data_import_export.urls', namespace='data_import_export')),
    ]
    
    # Store the original URLconf
    original_urlconf = settings.ROOT_URLCONF
    
    # Create a module to store the temporary URLconf
    import types
    urls_module = types.ModuleType('temp_urls')
    urls_module.urlpatterns = temp_urlpatterns
    
    # Set the temporary URLconf
    set_urlconf(urls_module)
    
    yield
    
    # Restore the original URLconf
    set_urlconf(original_urlconf)
    clear_url_caches()


@pytest.mark.django_db
class TestImportExportConfigViewSet:
    """Test cases for ImportExportConfigViewSet."""

    def test_list_configs(self, authenticated_client):
        """Test listing configs."""
        client, user = authenticated_client
        configs = [ImportExportConfigFactory(created_by=user) for _ in range(3)]
        
        url = reverse('data_import_export:importexportconfig-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == len(configs)

    def test_create_config(self, authenticated_client):
        """Test creating a config."""
        client, user = authenticated_client
        content_type = ContentTypeFactory()
        data = {
            'name': 'Test Config',
            'description': 'Test Description',
            'content_type_id': content_type.id,
            'field_mapping': {'source': 'target'},
            'is_active': True
        }
        
        url = reverse('data_import_export:importexportconfig-list')
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert ImportExportConfig.objects.count() == 1
        config = ImportExportConfig.objects.first()
        assert config.created_by == user

    def test_update_config(self, authenticated_client):
        """Test updating a config."""
        client, user = authenticated_client
        config = ImportExportConfigFactory(created_by=user)
        data = {
            'name': 'Updated Config',
            'description': 'Updated Description',
            'content_type_id': config.content_type.id,
            'field_mapping': {'new_source': 'new_target'},
            'is_active': False
        }
        
        url = reverse('data_import_export:importexportconfig-detail', kwargs={'pk': config.pk})
        response = client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        config.refresh_from_db()
        assert config.name == data['name']
        assert config.updated_by == user

    def test_validate_mapping(self, authenticated_client):
        """Test validating field mapping."""
        client, user = authenticated_client
        config = ImportExportConfigFactory(created_by=user)
        data = {
            'field_mapping': {
                'source_field': 'target_field',
                'name': 'name',
                'email': 'email'
            }
        }
        
        url = reverse('data_import_export:importexportconfig-validate-mapping', kwargs={'pk': config.pk})
        response = client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['valid'] is True

    def test_import_data(self, authenticated_client):
        """Test importing data."""
        client, user = authenticated_client
        config = ImportExportConfigFactory(created_by=user)
        
        # Create CSV file
        csv_content = 'name,email\nTest User,test@example.com'
        csv_file = io.StringIO(csv_content)
        csv_file.name = 'test.csv'  # Add name attribute
        
        url = reverse('data_import_export:importexportconfig-import-data', kwargs={'pk': config.pk})
        response = client.post(
            url,
            {'file': csv_file},
            format='multipart'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert ImportExportLog.objects.count() == 1

    def test_export_data(self, authenticated_client):
        """Test exporting data."""
        client, user = authenticated_client
        config = ImportExportConfigFactory(created_by=user)
        
        url = reverse('data_import_export:importexportconfig-export-data', kwargs={'pk': config.pk})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'
        assert 'attachment' in response['Content-Disposition']


@pytest.mark.django_db
class TestImportExportLogViewSet:
    """Test cases for ImportExportLogViewSet."""

    def test_list_logs(self, authenticated_client):
        """Test listing logs."""
        client, user = authenticated_client
        config = ImportExportConfigFactory(created_by=user)
        logs = [ImportExportLogFactory(config=config, performed_by=user) for _ in range(3)]
        
        url = reverse('data_import_export:importexportlog-list')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == len(logs)

    def test_retrieve_log(self, authenticated_client):
        """Test retrieving a log."""
        client, user = authenticated_client
        config = ImportExportConfigFactory(created_by=user)
        log = ImportExportLogFactory(config=config, performed_by=user)
        
        url = reverse('data_import_export:importexportlog-detail', kwargs={'pk': log.pk})
        response = client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == log.pk

    def test_retry_failed_log(self, authenticated_client):
        """Test retrying a failed log."""
        client, user = authenticated_client
        config = ImportExportConfigFactory(created_by=user)
        
        # Create CSV file for the original import
        csv_content = 'name,email\nTest User,test@example.com'
        csv_file = io.StringIO(csv_content)
        csv_file.name = 'test.csv'
        
        # Create a failed log with the file
        log = ImportExportLogFactory(
            config=config,
            performed_by=user,
            status=ImportExportLog.STATUS_FAILED,
            operation=ImportExportLog.OPERATION_IMPORT,
            file_name=csv_file.name,
            records_processed=1,
            records_succeeded=0,
            records_failed=1
        )
        
        url = reverse('data_import_export:importexportlog-retry', kwargs={'pk': log.pk})
        response = client.post(url, {'file': csv_file}, format='multipart')
        
        assert response.status_code == status.HTTP_200_OK
        assert ImportExportLog.objects.count() == 2

    def test_cannot_retry_completed_log(self, authenticated_client):
        """Test that completed logs cannot be retried."""
        client, user = authenticated_client
        config = ImportExportConfigFactory(created_by=user)
        log = ImportExportLogFactory(
            config=config,
            performed_by=user,
            status=ImportExportLog.STATUS_COMPLETED
        )
        
        url = reverse('data_import_export:importexportlog-retry', kwargs={'pk': log.pk})
        response = client.post(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
