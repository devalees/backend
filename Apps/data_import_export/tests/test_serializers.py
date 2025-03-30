import pytest
from django.contrib.contenttypes.models import ContentType
from ..serializers import (
    ContentTypeSerializer,
    ImportExportConfigSerializer,
    ImportExportLogSerializer
)
from .factories import (
    UserFactory,
    ContentTypeFactory,
    ImportExportConfigFactory,
    ImportExportLogFactory
)


@pytest.mark.django_db
class TestContentTypeSerializer:
    """Test cases for ContentTypeSerializer."""

    def test_serialize_content_type(self):
        """Test serializing a content type."""
        content_type = ContentTypeFactory()
        serializer = ContentTypeSerializer(content_type)
        data = serializer.data
        
        assert data['id'] == content_type.id
        assert data['app_label'] == content_type.app_label
        assert data['model'] == content_type.model


@pytest.mark.django_db
class TestImportExportConfigSerializer:
    """Test cases for ImportExportConfigSerializer."""

    def test_serialize_config(self):
        """Test serializing a config."""
        config = ImportExportConfigFactory()
        serializer = ImportExportConfigSerializer(config)
        data = serializer.data
        
        assert data['name'] == config.name
        assert data['description'] == config.description
        assert data['field_mapping'] == config.field_mapping
        assert data['is_active'] == config.is_active

    def test_create_config(self):
        """Test creating a config through serializer."""
        user = UserFactory()
        content_type = ContentTypeFactory()
        data = {
            'name': 'Test Config',
            'description': 'Test Description',
            'content_type_id': content_type.id,
            'field_mapping': {'source': 'target'},
            'is_active': True
        }
        
        serializer = ImportExportConfigSerializer(data=data, context={'request': type('Request', (), {'user': user})()})
        assert serializer.is_valid()
        
        config = serializer.save()
        assert config.name == data['name']
        assert config.created_by == user

    def test_update_config(self):
        """Test updating a config through serializer."""
        config = ImportExportConfigFactory()
        user = config.created_by
        data = {
            'name': 'Updated Config',
            'description': 'Updated Description',
            'content_type_id': config.content_type.id,
            'field_mapping': {'new_source': 'new_target'},
            'is_active': False
        }
        
        serializer = ImportExportConfigSerializer(config, data=data, context={'request': type('Request', (), {'user': user})()})
        assert serializer.is_valid()
        
        updated_config = serializer.save()
        assert updated_config.name == data['name']
        assert updated_config.field_mapping == data['field_mapping']

    def test_validate_field_mapping(self):
        """Test field mapping validation."""
        data = {
            'name': 'Test Config',
            'content_type_id': ContentTypeFactory().id,
            'field_mapping': {}  # Empty mapping should fail
        }
        
        serializer = ImportExportConfigSerializer(data=data)
        assert not serializer.is_valid()
        assert 'field_mapping' in serializer.errors


@pytest.mark.django_db
class TestImportExportLogSerializer:
    """Test cases for ImportExportLogSerializer."""

    def test_serialize_log(self):
        """Test serializing a log."""
        log = ImportExportLogFactory()
        serializer = ImportExportLogSerializer(log)
        data = serializer.data
        
        assert data['config']['id'] == log.config.id
        assert data['operation'] == log.operation
        assert data['status'] == log.status
        assert data['file_name'] == log.file_name
        assert data['records_processed'] == log.records_processed
        assert float(data['success_rate']) == log.success_rate

    def test_create_log(self):
        """Test creating a log through serializer."""
        config = ImportExportConfigFactory()
        user = UserFactory()
        data = {
            'config_id': config.id,
            'operation': 'import',
            'file_name': 'test.csv',
            'records_processed': 100,
            'records_succeeded': 90,
            'records_failed': 10,
            'status': 'completed'
        }
        
        serializer = ImportExportLogSerializer(data=data, context={'request': type('Request', (), {'user': user})()})
        assert serializer.is_valid()
        
        log = serializer.save()
        assert log.config == config
        assert log.performed_by == user
        assert log.success_rate == 90.0

    def test_validate_records_count(self):
        """Test validation of records count."""
        config = ImportExportConfigFactory()
        data = {
            'config_id': config.id,
            'operation': 'import',
            'file_name': 'test.csv',
            'records_processed': 50,
            'records_succeeded': 60,  # More successes than processed
            'records_failed': 0,
            'status': 'completed'
        }
        
        serializer = ImportExportLogSerializer(data=data)
        assert not serializer.is_valid()
        assert 'records_succeeded' in serializer.errors
