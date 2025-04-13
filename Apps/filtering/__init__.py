# This file is intentionally left mostly empty to avoid circular imports
# The actual imports will be handled by the AppConfig in apps.py

# Define __all__ to specify what should be imported with "from filtering import *"
__all__ = [
    # Base classes
    'BaseFilterableModel',
    'BaseAggregatableModel',
    'BaseFilterRegistry',
    'BaseAggregationRegistry',
    
    # Mixins
    'FilterableMixin',
    'AggregatableMixin',
    'ModelRegistryMixin',
    
    # Registry
    'model_registry',
    'ModelRegistry',
    
    # Filters
    'text_filter',
    'numeric_filter',
    'date_filter',
    'time_filter',
    'boolean_filter',
    'choice_filter',
    'related_object_filter',
    
    # Aggregations
    'count_aggregation',
    'sum_aggregation',
    'avg_aggregation',
    'min_aggregation',
    'max_aggregation',
    'custom_aggregation',
    'get_aggregation',
    'aggregation_registry'
]

# These will be populated by the AppConfig when Django is ready
BaseFilterableModel = None
BaseAggregatableModel = None
BaseFilterRegistry = None
BaseAggregationRegistry = None
ModelRegistry = None
FilterableMixin = None
AggregatableMixin = None
ModelRegistryMixin = None
FilterValidationError = None
FieldTypeValidator = None
OperatorValidator = None
ValueValidator = None
FilterValidator = None
FilterFactory = None
BasicFilterFactory = None
AdvancedFilterFactory = None
FilterTypeMapping = None 