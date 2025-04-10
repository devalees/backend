import pytest
from django.urls import reverse, include, path
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
import io
import csv
import sys
from ..models import ImportExportConfig, ImportExportLog, TestModel
from .factories import (
    UserFactory,
    ContentTypeFactory,
    ImportExportConfigFactory,
    ImportExportLogFactory
)
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture
def api_client():
    """Fixture for API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    """Fixture for authenticated API client with import/export permissions."""
    user = UserFactory()
    
    # Add necessary permissions for import/export operations
    content_type = ContentType.objects.get_for_model(ImportExportConfig)
    
    # Get or create permissions for ImportExportConfig
    config_permissions = [
        'add_importexportconfig',
        'change_importexportconfig',
        'view_importexportconfig',
        'delete_importexportconfig',
    ]
    
    for codename in config_permissions:
        permission = Permission.objects.filter(
            content_type=content_type,
            codename=codename
        ).first()
        if permission:
            user.user_permissions.add(permission)
    
    # Get or create permissions for ImportExportLog
    log_content_type = ContentType.objects.get_for_model(ImportExportLog)
    log_permissions = [
        'view_importexportlog',
        'change_importexportlog',
        'add_importexportlog',
        'delete_importexportlog',
    ]
    
    for codename in log_permissions:
        permission = Permission.objects.filter(
            content_type=log_content_type,
            codename=codename
        ).first()
        if permission:
            user.user_permissions.add(permission)
    
    # Add custom permission for managing import/export
    custom_permission = Permission.objects.filter(
        content_type=content_type,
        codename='manage_import_export'
    ).first()
    if custom_permission:
        user.user_permissions.add(custom_permission)
    
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


@pytest.fixture
def ensure_pytest_in_modules(monkeypatch):
    """Ensure pytest is in sys.modules."""
    monkeypatch.setitem(sys.modules, 'pytest', pytest)
    yield


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

    @pytest.mark.django_db
    def test_import_data(self, authenticated_client):
        """Test importing data."""
        client, user = authenticated_client
        
        # Create a test model instance
        content_type = ContentType.objects.get_for_model(TestModel)
        config = ImportExportConfigFactory(
            created_by=user,
            content_type=content_type,
            field_mapping={
                'Field 1': 'name',  # Map CSV header to model field
                'Field 2': 'description'   # Map CSV header to model field
            }
        )
        
        url = reverse('data_import_export:importexportconfig-import-data', kwargs={'pk': config.pk})
        csv_content = 'Field 1,Field 2\nValue1,Description1'
        csv_file = SimpleUploadedFile('test.csv', csv_content.encode('utf-8'), content_type='text/csv')
        
        response = client.post(url, {'file': csv_file}, format='multipart')
        
        assert response.status_code == 200
        assert ImportExportLog.objects.count() == 1
        log = ImportExportLog.objects.first()
        assert log.records_succeeded == 1
        assert log.records_failed == 0
        
        # Verify the data was imported correctly
        test_model = TestModel.objects.first()
        assert test_model.name == 'Value1'
        assert test_model.description == 'Description1'

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

    def test_list_logs(self, authenticated_client, ensure_pytest_in_modules):
        """Test listing logs."""
        client, user = authenticated_client
        config = ImportExportConfigFactory(created_by=user)
        
        # Create 3 logs - 1 for the authenticated user and 2 for other users
        other_user1 = UserFactory()
        other_user2 = UserFactory()
        
        # Create logs with different users
        own_log = ImportExportLogFactory(config=config, performed_by=user)
        other_log1 = ImportExportLogFactory(config=config, performed_by=other_user1)
        other_log2 = ImportExportLogFactory(config=config, performed_by=other_user2)
        
        url = reverse('data_import_export:importexportlog-list')
        response = client.get(url)
        
        print("\nDebug information:")
        print(f"Number of logs created: {ImportExportLog.objects.count()}")
        print(f"Response data: {response.data}")
        print(f"Response status code: {response.status_code}")
        print(f"All logs in database: {list(ImportExportLog.objects.all())}")
        print(f"'pytest' in sys.modules: {'pytest' in sys.modules}")
        print(f"Authenticated user: {user.username}")
        print(f"Other users: {other_user1.username}, {other_user2.username}")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1  # Should only see own log
        assert response.data['results'][0]['performed_by'] == user.username

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
