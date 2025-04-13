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
        from .filter_factory import (
            FilterFactory,
            BasicFilterFactory,
            AdvancedFilterFactory,
            FilterTypeMapping
        )
        from .aggregations import (
            count_aggregation,
            sum_aggregation,
            avg_aggregation,
            min_aggregation,
            max_aggregation,
            custom_aggregation,
            get_aggregation,
            aggregation_registry
        )
        from .aggregation_validation import (
            AggregationFieldValidator,
            AggregationTypeValidator,
            AggregationGroupValidator,
            AggregationValidator
        )
        # Import model discovery service
        from .model_discovery import ModelDiscoveryService
        
        # Import model auto-discovery helpers
        from .model_auto_discovery import (
            discover_and_register_app_models,
            discover_and_register_all_models,
            generate_model_report,
            # New automatic mixin application functions
            discover_and_enhance_app_models,
            discover_and_enhance_all_models,
            enhance_existing_model
        )
        
        # Import automatic mixin application module
        from .auto_mixin_applier import (
            AutoMixinApplier,
            apply_mixins_to_model,
            apply_indexes_to_model,
            register_model_indexes
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
        Apps.filtering.FilterFactory = FilterFactory
        Apps.filtering.BasicFilterFactory = BasicFilterFactory
        Apps.filtering.AdvancedFilterFactory = AdvancedFilterFactory
        Apps.filtering.FilterTypeMapping = FilterTypeMapping
        
        # Expose the aggregation functions
        Apps.filtering.count_aggregation = count_aggregation
        Apps.filtering.sum_aggregation = sum_aggregation
        Apps.filtering.avg_aggregation = avg_aggregation
        Apps.filtering.min_aggregation = min_aggregation
        Apps.filtering.max_aggregation = max_aggregation
        Apps.filtering.custom_aggregation = custom_aggregation
        Apps.filtering.get_aggregation = get_aggregation
        Apps.filtering.aggregation_registry = aggregation_registry
        
        # Expose the aggregation validation classes
        Apps.filtering.AggregationFieldValidator = AggregationFieldValidator
        Apps.filtering.AggregationTypeValidator = AggregationTypeValidator
        Apps.filtering.AggregationGroupValidator = AggregationGroupValidator
        Apps.filtering.AggregationValidator = AggregationValidator
        
        # Expose the model discovery service
        Apps.filtering.ModelDiscoveryService = ModelDiscoveryService
        
        # Expose model auto-discovery functions
        Apps.filtering.discover_and_register_app_models = discover_and_register_app_models
        Apps.filtering.discover_and_register_all_models = discover_and_register_all_models
        Apps.filtering.generate_model_report = generate_model_report
        
        # Expose automatic mixin application functions
        Apps.filtering.discover_and_enhance_app_models = discover_and_enhance_app_models
        Apps.filtering.discover_and_enhance_all_models = discover_and_enhance_all_models
        Apps.filtering.enhance_existing_model = enhance_existing_model
        Apps.filtering.AutoMixinApplier = AutoMixinApplier
        Apps.filtering.apply_mixins_to_model = apply_mixins_to_model
        Apps.filtering.apply_indexes_to_model = apply_indexes_to_model
        Apps.filtering.register_model_indexes = register_model_indexes 