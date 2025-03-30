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
from .models_for_testing import TestModel, NonImportExportModel


@pytest.mark.django_db
class TestImportExportConfig:
    """Test cases for ImportExportConfig model."""

    def test_create_config(self):
        """Test creating a config with valid data."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config = ImportExportConfigFactory(content_type=content_type)
        assert config.pk is not None
        assert config.name.startswith('Config')
        assert config.is_active is True

    def test_field_mapping_validation(self):
        """Test field mapping validation."""
        content_type = ContentType.objects.get_for_model(TestModel)
        # Test empty field mapping
        config = ImportExportConfigFactory.build(
            content_type=content_type,
            field_mapping={}
        )
        with pytest.raises(ValidationError) as exc:
            config.full_clean()
        assert 'Field mapping cannot be empty' in str(exc.value)

        # Test non-dict field mapping
        config = ImportExportConfigFactory.build(
            content_type=content_type,
            field_mapping=['not', 'a', 'dict']
        )
        with pytest.raises(ValidationError) as exc:
            config.full_clean()
        assert 'Field mapping must be a dictionary' in str(exc.value)

    def test_unique_name_per_content_type(self):
        """Test that names must be unique per content type."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config1 = ImportExportConfigFactory(content_type=content_type)
        config2 = ImportExportConfigFactory.build(
            name=config1.name,
            content_type=content_type
        )
        with pytest.raises(ValidationError):
            config2.full_clean()

    def test_str_representation(self):
        """Test string representation of config."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config = ImportExportConfigFactory(content_type=content_type)
        assert str(config) == f"{config.name} ({content_type.model})"

    def test_audit_fields(self):
        """Test audit fields are properly set."""
        content_type = ContentType.objects.get_for_model(TestModel)
        user = UserFactory()
        config = ImportExportConfigFactory(
            content_type=content_type,
            created_by=user,
            updated_by=user
        )
        assert config.created_by == user
        assert config.updated_by == user
        assert config.created_at is not None
        assert config.updated_at is not None


@pytest.mark.django_db
class TestImportExportLog:
    """Test cases for ImportExportLog model."""

    def test_create_log(self):
        """Test creating a log with valid data."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config = ImportExportConfigFactory(content_type=content_type)
        log = ImportExportLogFactory(config=config)
        assert log.pk is not None
        assert log.operation in ['import', 'export']
        assert log.status in ['in_progress', 'completed', 'failed']

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config = ImportExportConfigFactory(content_type=content_type)
        log = ImportExportLogFactory(
            config=config,
            records_processed=100,
            records_succeeded=80,
            records_failed=20
        )
        assert log.success_rate == 80.0

    def test_status_transitions(self):
        """Test valid status transitions."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config = ImportExportConfigFactory(content_type=content_type)
        log = ImportExportLogFactory(config=config)
        
        # Test valid transitions
        log.status = ImportExportLog.STATUS_IN_PROGRESS
        log.full_clean()
        log.save()
        
        log.status = ImportExportLog.STATUS_COMPLETED
        log.full_clean()
        log.save()
        
        # Test invalid transition
        with pytest.raises(ValidationError):
            log.status = 'invalid_status'
            log.full_clean()
            log.save()

    def test_operation_choices(self):
        """Test operation choices validation."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config = ImportExportConfigFactory(content_type=content_type)
        log = ImportExportLogFactory(config=config)
        assert log.operation in dict(ImportExportLog.OPERATION_CHOICES)

    def test_str_representation(self):
        """Test string representation of log."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config = ImportExportConfigFactory(content_type=content_type)
        log = ImportExportLogFactory(config=config)
        assert str(log) == f"{log.operation.title()}: {log.file_name} ({log.status})"

    def test_records_validation(self):
        """Test records count validation."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config = ImportExportConfigFactory(content_type=content_type)
        log = ImportExportLogFactory.build(
            config=config,
            records_processed=100,
            records_succeeded=60,
            records_failed=50
        )
        with pytest.raises(ValidationError):
            log.full_clean()

    @pytest.mark.parametrize('status,expected_is_failed', [
        (ImportExportLog.STATUS_FAILED, True),
        (ImportExportLog.STATUS_COMPLETED, False),
        (ImportExportLog.STATUS_IN_PROGRESS, False),
    ])
    def test_is_failed_property(self, status, expected_is_failed):
        """Test is_failed property based on status."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config = ImportExportConfigFactory(content_type=content_type)
        log = ImportExportLogFactory(config=config, status=status)
        assert log.is_failed == expected_is_failed
