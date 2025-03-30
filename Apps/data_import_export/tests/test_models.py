import pytest
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.db import models
from ..models import ImportExportConfig, ImportExportLog
from .factories import (
    UserFactory,
    ContentTypeFactory,
    ImportExportConfigFactory,
    ImportExportLogFactory
)


class TestModel(models.Model):
    """Test model for import/export functionality."""
    name = models.CharField(max_length=100)
    
    class Meta:
        app_label = 'data_import_export'
        
    @classmethod
    def is_import_export_enabled(cls):
        return True


@pytest.mark.django_db
class TestImportExportConfig:
    """Test cases for ImportExportConfig model."""

    def test_create_config(self):
        """Test creating a config with valid data."""
        config = ImportExportConfigFactory()
        assert config.pk is not None
        assert config.name.startswith('Config')
        assert config.is_active is True

    def test_field_mapping_validation(self):
        """Test field mapping validation."""
        # Test empty field mapping
        config = ImportExportConfigFactory.build(field_mapping={})
        with pytest.raises(ValidationError) as exc:
            config.full_clean()
        assert 'Field mapping cannot be empty' in str(exc.value)

        # Test non-dict field mapping
        config = ImportExportConfigFactory.build(field_mapping=['not', 'a', 'dict'])
        with pytest.raises(ValidationError) as exc:
            config.full_clean()
        assert 'Field mapping must be a dictionary' in str(exc.value)

    def test_unique_name_per_content_type(self):
        """Test that names must be unique per content type."""
        config1 = ImportExportConfigFactory()
        config2 = ImportExportConfigFactory.build(
            name=config1.name,
            content_type=config1.content_type
        )
        with pytest.raises(ValidationError):
            config2.full_clean()

    def test_str_representation(self):
        """Test string representation of config."""
        config = ImportExportConfigFactory(name='Test Config')
        assert str(config) == 'Test Config'

    def test_audit_fields(self):
        """Test audit fields are set correctly."""
        user = UserFactory()
        config = ImportExportConfigFactory(created_by=user)
        assert config.created_by == user
        assert config.updated_by == user


@pytest.mark.django_db
class TestImportExportLog:
    """Test cases for ImportExportLog model."""

    def test_create_log(self):
        """Test creating a log with valid data."""
        log = ImportExportLogFactory()
        assert log.pk is not None
        assert log.file_name.startswith('test_file_')
        assert log.records_processed >= 0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        log = ImportExportLogFactory(
            records_processed=100,
            records_succeeded=75
        )
        assert log.success_rate == 75.0

    def test_status_transitions(self):
        """Test status transitions."""
        log = ImportExportLogFactory(status=ImportExportLog.STATUS_IN_PROGRESS)
        assert log.status == ImportExportLog.STATUS_IN_PROGRESS
        
        log.status = ImportExportLog.STATUS_COMPLETED
        log.save()
        assert log.status == ImportExportLog.STATUS_COMPLETED

    def test_operation_choices(self):
        """Test operation choices."""
        log = ImportExportLogFactory(operation=ImportExportLog.OPERATION_IMPORT)
        assert log.operation in [ImportExportLog.OPERATION_IMPORT, ImportExportLog.OPERATION_EXPORT]

    def test_str_representation(self):
        """Test string representation of log."""
        log = ImportExportLogFactory(
            file_name='test.csv',
            operation=ImportExportLog.OPERATION_IMPORT
        )
        expected = f'Import: test.csv ({log.status})'
        assert str(log) == expected

    def test_records_validation(self):
        """Test records count validation."""
        log = ImportExportLogFactory.build(
            records_processed=50,
            records_succeeded=75,
            records_failed=0
        )
        with pytest.raises(ValidationError):
            log.full_clean()

    @pytest.mark.parametrize('status,expected_is_failed', [
        (ImportExportLog.STATUS_FAILED, True),
        (ImportExportLog.STATUS_COMPLETED, False),
        (ImportExportLog.STATUS_IN_PROGRESS, False),
    ])
    def test_is_failed_property(self, status, expected_is_failed):
        """Test is_failed property."""
        log = ImportExportLogFactory(status=status)
        assert log.is_failed is expected_is_failed
