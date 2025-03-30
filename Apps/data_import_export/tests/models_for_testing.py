from django.db import models

class TestModel(models.Model):
    """Test model for import/export functionality."""
    field1 = models.CharField(max_length=100)
    field2 = models.IntegerField()
    
    class Meta:
        app_label = 'data_import_export'
        
    @classmethod
    def is_import_export_enabled(cls):
        return True


class NonImportExportModel(models.Model):
    field1 = models.CharField(max_length=100)
    field2 = models.IntegerField()

    class Meta:
        app_label = 'data_import_export'

    @classmethod
    def is_import_export_enabled(cls):
        return False 