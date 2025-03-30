from django.db import models
from django.contrib.contenttypes.models import ContentType

class ImportExportMixin:
    """Mixin to add import/export capabilities to any model."""
    
    import_export_enabled = True
    import_export_fields = None  # List of fields to include in import/export
    
    @classmethod
    def get_import_export_fields(cls):
        """Get the list of fields to include in import/export."""
        if cls.import_export_fields is not None:
            return cls.import_export_fields
        return [field.name for field in cls._meta.fields if not field.is_relation]
    
    @classmethod
    def is_import_export_enabled(cls):
        """Check if the model has import/export enabled."""
        return getattr(cls, 'import_export_enabled', False)
        
    @staticmethod
    def get_import_export_enabled_models():
        """Get all models that have import/export enabled."""
        enabled_models = []
        for model in ContentType.objects.all():
            model_class = model.model_class()
            if model_class and hasattr(model_class, 'is_import_export_enabled'):
                if model_class.is_import_export_enabled():
                    enabled_models.append(model.model)
        return enabled_models 