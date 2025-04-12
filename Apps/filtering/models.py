from django.db import models
from .base import BaseFilterableModel, BaseAggregatableModel
from .mixins import FilterableMixin, AggregatableMixin, ModelRegistryMixin

class TestFilterableModel(BaseFilterableModel, FilterableMixin, ModelRegistryMixin):
    name = models.CharField(max_length=100)
    description = models.TextField()
    age = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'filtering'

class TestAggregatableModel(BaseAggregatableModel, AggregatableMixin, ModelRegistryMixin):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'filtering'

class TestCombinedModel(BaseFilterableModel, BaseAggregatableModel, FilterableMixin, AggregatableMixin, ModelRegistryMixin):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'filtering'

class TestModelRegistryModel(BaseFilterableModel, ModelRegistryMixin):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'filtering' 