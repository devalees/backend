from django.apps import AppConfig
import importlib


class FilteringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Apps.filtering'
    verbose_name = 'Filtering'
    
    def ready(self):
        """
        Import and expose models when the app is ready.
        This is called after Django has fully initialized.
        """
        # Import the models
        from .base import (
            BaseFilterableModel,
            BaseAggregatableModel,
            BaseFilterRegistry,
            BaseAggregationRegistry
        )
        from .registry import ModelRegistry
        from .mixins import FilterableMixin, AggregatableMixin, ModelRegistryMixin
        from .filter_validation import (
            FilterValidationError,
            FieldTypeValidator,
            OperatorValidator,
            ValueValidator,
            FilterValidator
        )
        
        # Import the __init__.py module properly
        import Apps.filtering
        
        # Expose the models in the package namespace
        Apps.filtering.BaseFilterableModel = BaseFilterableModel
        Apps.filtering.BaseAggregatableModel = BaseAggregatableModel
        Apps.filtering.BaseFilterRegistry = BaseFilterRegistry
        Apps.filtering.BaseAggregationRegistry = BaseAggregationRegistry
        Apps.filtering.ModelRegistry = ModelRegistry
        Apps.filtering.FilterableMixin = FilterableMixin
        Apps.filtering.AggregatableMixin = AggregatableMixin
        Apps.filtering.ModelRegistryMixin = ModelRegistryMixin
        Apps.filtering.FilterValidationError = FilterValidationError
        Apps.filtering.FieldTypeValidator = FieldTypeValidator
        Apps.filtering.OperatorValidator = OperatorValidator
        Apps.filtering.ValueValidator = ValueValidator
        Apps.filtering.FilterValidator = FilterValidator 