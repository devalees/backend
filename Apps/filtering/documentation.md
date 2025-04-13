# Django Filtering and Aggregation System

## Overview

The Django Filtering and Aggregation System provides a powerful and flexible way to add advanced filtering and aggregation capabilities to your Django models. This system allows you to:

1. Specify which fields should be available for filtering and aggregation
2. Automatically register models for filtering and aggregation
3. Configure different types of filters and aggregations based on field types
4. Create indexes for optimal query performance

## Installation

The filtering system is integrated into the Django project and does not require additional installation steps.

## Usage

### Basic Model Configuration

To make a model filterable and/or aggregatable, you can inherit from one of the provided base model classes:

```python
from Apps.filtering.base_model import (
    FilterableModel, 
    AggregatableModel, 
    FilterableAggregatableModel
)

# For filtering only
class YourFilterableModel(FilterableModel):
    name = models.CharField(max_length=100)
    
    class FilterConfig:
        text = ['name']

# For aggregation only
class YourAggregatableModel(AggregatableModel):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class AggregationConfig:
        sum = ['amount']

# For both filtering and aggregation
class YourCombinedModel(FilterableAggregatableModel):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class FilterConfig:
        text = ['name']
        
    class AggregationConfig:
        sum = ['amount']
```

### Model Configuration Options

#### Filter Configuration

You can configure filtering by adding a `FilterConfig` inner class to your model:

```python
class YourModel(FilterableModel):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class FilterConfig:
        # Field types
        text = ['name']
        numeric = ['price']
        date = ['created_at']
        boolean = ['is_active']
        
        # Performance configuration
        indexes = [
            ['name'],
            ['created_at', 'is_active']
        ]
```

Supported filter field types:
- `text`: For text-based fields (CharField, TextField)
- `numeric`: For numeric fields (IntegerField, DecimalField, FloatField)
- `date`: For date fields (DateField)
- `time`: For time fields (TimeField)
- `datetime`: For datetime fields (DateTimeField)
- `boolean`: For boolean fields (BooleanField)
- `choice`: For fields with choices
- `related`: For related fields (ForeignKey, ManyToMany)

#### Aggregation Configuration

You can configure aggregation by adding an `AggregationConfig` inner class to your model:

```python
class YourModel(AggregatableModel):
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    category = models.ForeignKey('Category', on_delete=models.CASCADE)
    
    class AggregationConfig:
        # Grouping fields
        group_by = ['category']
        
        # Aggregation fields
        sum = ['price', 'quantity']
        avg = ['price']
        min = ['price']
        max = ['price']
        count = ['id']
```

Supported aggregation types:
- `group_by`: Fields to group by
- `sum`: Fields to sum
- `avg`: Fields to average
- `min`: Fields to find minimum
- `max`: Fields to find maximum
- `count`: Fields to count

### Automatic Discovery and Registration

The system automatically registers your models when they inherit from one of the base model classes. However, you can also explicitly discover and register existing models:

```python
from Apps.filtering.model_registry import model_registry

# Discover models in specific apps
model_registry.discover_models(app_labels=['myapp', 'otherapp'])

# Register all discovered models
model_registry.register_discovered_models()
```

## API Reference

### Base Model Classes

- `FilterableModel`: Base model class for filtering capabilities
- `AggregatableModel`: Base model class for aggregation capabilities
- `FilterableAggregatableModel`: Base model class for both filtering and aggregation

### Model Registry

The `model_registry` is a singleton instance that manages all registered models:

```python
from Apps.filtering.model_registry import model_registry

# Register a model
model_registry.register(YourModel)

# Unregister a model
model_registry.unregister(YourModel)

# Check if a model is registered
is_registered = model_registry.is_registered(YourModel)

# Get model configuration
config = model_registry.get_config(YourModel)

# Discover models
model_registry.discover_models()

# Register all discovered models
model_registry.register_discovered_models()

# Get all registered models
registered_models = model_registry.registered_models

# Get all discovered but not yet registered models
discovered_models = model_registry.discovered_models
```

### Model Configuration

The `ModelConfig` class manages model-specific configurations:

```python
from Apps.filtering.model_config import ModelConfig

# Create a configuration for a model
config = ModelConfig(YourModel)

# Get filter fields
all_filters = config.get_filter_fields()
text_filters = config.get_filter_fields('text')

# Get aggregation fields
all_aggregations = config.get_aggregation_fields()
sum_aggregations = config.get_aggregation_fields('sum')

# Get indexes
indexes = config.get_indexes()
```

## Best Practices

1. **Specify Field Types Explicitly**: Always specify the field types explicitly in your FilterConfig and AggregationConfig classes to ensure proper filter and aggregation handling.

2. **Configure Indexes**: Define indexes for fields that will be frequently filtered or aggregated to optimize query performance.

3. **Limit Filter Fields**: Only expose fields that really need to be filtered to minimize overhead and potential security risks.

4. **Group Related Fields**: When defining filters and aggregations, group related fields together for better organization.

5. **Test Thoroughly**: Use the test suite to ensure your filter and aggregation configurations work as expected.

## Troubleshooting

### Common Issues

1. **Model Not Registered**: If your model is not being registered automatically, check if it's inheriting from one of the base model classes and doesn't have `abstract = True` in its Meta class.

2. **Field Not Available for Filtering**: Ensure the field is specified in the correct field type list in the FilterConfig class.

3. **Field Not Available for Aggregation**: Check if the field is specified in the appropriate aggregation type list in the AggregationConfig class.

4. **Performance Issues**: Consider adding indexes for frequently filtered fields.

## Contributing

To contribute to the filtering system:

1. Add tests for your changes
2. Maintain test coverage of at least 90%
3. Update documentation to reflect your changes
4. Follow Django's coding style 