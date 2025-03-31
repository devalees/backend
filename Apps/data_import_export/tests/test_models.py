import pytest
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.db import models
from ..models import ImportExportConfig, ImportExportLog, TestModel, NonImportExportModel
from .factories import (
    UserFactory,
    ContentTypeFactory,
    ImportExportConfigFactory,
    ImportExportLogFactory
)
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
import time

User = get_user_model()


@pytest.mark.django_db
class TestImportExportConfig(TestCase):
    """Test cases for ImportExportConfig model."""

    def test_create_config(self):
        """Test creating a config with valid data."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config = ImportExportConfigFactory(content_type=content_type)
        self.assertIsNotNone(config.pk)
        self.assertTrue(config.name.startswith('Config'))
        self.assertTrue(config.is_active)

    def test_field_mapping_validation(self):
        """Test field mapping validation."""
        config = ImportExportConfigFactory.build()
        
        # Test empty field mapping
        config.field_mapping = {}
        with pytest.raises(ValidationError, match='Field mapping cannot be empty'):
            config.clean()
        
        # Test invalid field mapping type
        config.field_mapping = []
        with pytest.raises(ValidationError, match='Field mapping must be a dictionary'):
            config.clean()
        
        # Test invalid target field
        config.field_mapping = {'source_field': 'invalid_field'}
        with pytest.raises(ValidationError, match='Invalid target field: invalid_field'):
            config.clean()
        
        # Test valid field mapping
        config.field_mapping = {'source_field': 'name', 'description_field': 'description'}
        config.clean()  # Should not raise any validation errors

    def test_unique_name_per_content_type(self):
        """Test that names must be unique per content type."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config1 = ImportExportConfigFactory(content_type=content_type)
        config2 = ImportExportConfigFactory.build(
            name=config1.name,
            content_type=content_type
        )
        with self.assertRaises(ValidationError):
            config2.full_clean()

    def test_str_representation(self):
        """Test string representation of config."""
        content_type = ContentType.objects.get_for_model(TestModel)
        config = ImportExportConfigFactory(content_type=content_type)
        self.assertEqual(str(config), f"{config.name} ({content_type.model})")

    def test_audit_fields(self):
        """Test audit fields are properly set."""
        content_type = ContentType.objects.get_for_model(TestModel)
        user = UserFactory()
        config = ImportExportConfigFactory(
            content_type=content_type,
            created_by=user,
            updated_by=user
        )
        self.assertEqual(config.created_by, user)
        self.assertEqual(config.updated_by, user)
        self.assertIsNotNone(config.created_at)
        self.assertIsNotNone(config.updated_at)


@pytest.mark.django_db
class TestImportExportLog(TestCase):
    """Test cases for ImportExportLog model."""

    def test_create_log(self):
        """Test creating a new import/export log."""
        config = ImportExportConfigFactory()
        user = UserFactory()
        log = ImportExportLog.objects.create(
            config=config,
            operation=ImportExportLog.OPERATION_IMPORT,
            file_name='test.csv',
            performed_by=user
        )
        
        self.assertEqual(log.config, config)
        self.assertEqual(log.operation, ImportExportLog.OPERATION_IMPORT)
        self.assertEqual(log.status, ImportExportLog.STATUS_IN_PROGRESS)
        self.assertEqual(log.file_name, 'test.csv')
        self.assertEqual(log.performed_by, user)
        self.assertEqual(log.records_processed, 0)
        self.assertEqual(log.records_succeeded, 0)
        self.assertEqual(log.records_failed, 0)
        self.assertEqual(log.error_message, '')
        self.assertIsNotNone(log.created_at)
        self.assertIsNotNone(log.updated_at)

    def test_log_str_representation(self):
        """Test string representation."""
        log = ImportExportLogFactory()
        expected = f"{log.operation.title()}: {log.file_name} ({log.status})"
        self.assertEqual(str(log), expected)

    def test_log_status_properties(self):
        """Test status properties."""
        log = ImportExportLogFactory(status=ImportExportLog.STATUS_FAILED)
        self.assertTrue(log.is_failed)

    def test_log_success_rate(self):
        """Test success rate calculation."""
        log = ImportExportLogFactory(
            records_processed=100,
            records_succeeded=75,
            records_failed=25
        )
        self.assertEqual(log.success_rate, 75.0)

    def test_log_success_rate_zero_processed(self):
        """Test success rate when no records processed."""
        log = ImportExportLogFactory(
            records_processed=0,
            records_succeeded=0,
            records_failed=0
        )
        self.assertEqual(log.success_rate, 0.0)

    def test_log_timestamps(self):
        """Test that timestamps are properly set and updated."""
        log = ImportExportLogFactory()
        original_updated_at = log.updated_at
        time.sleep(0.1)  # Ensure time difference
        log.save()
        self.assertGreater(log.updated_at, original_updated_at)

    def test_log_validation(self):
        """Test log validation rules."""
        log = ImportExportLogFactory()
        log.records_processed = -1
        with self.assertRaises(ValidationError):
            log.full_clean()

    def test_log_status_change(self):
        """Test that completed logs cannot change status."""
        log = ImportExportLogFactory(status=ImportExportLog.STATUS_COMPLETED)
        with self.assertRaises(ValidationError):
            log.status = ImportExportLog.STATUS_FAILED
            log.full_clean()

    def test_log_indexes(self):
        """Test that indexes are properly set."""
        log = ImportExportLogFactory()
        self.assertIsNotNone(log.created_at)
        self.assertIsNotNone(log.updated_at)
