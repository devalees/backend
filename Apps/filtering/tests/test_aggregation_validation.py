from django.test import TestCase
from django.db import models
from django.core.exceptions import ValidationError
from ..base import BaseAggregatableModel
from ..aggregation_validation import (
    AggregationFieldValidator,
    AggregationTypeValidator,
    AggregationGroupValidator,
    AggregationValidator
)

# Test model for validation
class ValidationTestModel(BaseAggregatableModel):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    category = models.CharField(max_length=100)

class TestAggregationValidation(TestCase):
    def setUp(self):
        self.field_validator = AggregationFieldValidator()
        self.type_validator = AggregationTypeValidator()
        self.group_validator = AggregationGroupValidator()
        self.validator = AggregationValidator()
        
        # Create test data
        ValidationTestModel.objects.create(
            name="Test 1",
            value=10,
            price=100.50,
            date="2024-01-01",
            category="A"
        )
        ValidationTestModel.objects.create(
            name="Test 2",
            value=20,
            price=200.75,
            date="2024-01-02",
            category="A"
        )
        ValidationTestModel.objects.create(
            name="Test 3",
            value=30,
            price=300.25,
            date="2024-01-03",
            category="B"
        )

    def test_field_validator_valid_fields(self):
        """Test that field validator accepts valid aggregatable fields"""
        # Test numeric fields
        self.assertTrue(self.field_validator.validate("value", ValidationTestModel))
        self.assertTrue(self.field_validator.validate("price", ValidationTestModel))

    def test_field_validator_invalid_fields(self):
        """Test that field validator rejects non-aggregatable fields"""
        with self.assertRaises(ValidationError):
            self.field_validator.validate("name", ValidationTestModel)
        with self.assertRaises(ValidationError):
            self.field_validator.validate("nonexistent", ValidationTestModel)

    def test_type_validator_valid_types(self):
        """Test that type validator accepts valid aggregation types"""
        valid_types = ["sum", "avg", "min", "max", "count"]
        for agg_type in valid_types:
            self.assertTrue(self.type_validator.validate(agg_type, "value", ValidationTestModel))

    def test_type_validator_invalid_types(self):
        """Test that type validator rejects invalid aggregation types"""
        with self.assertRaises(ValidationError):
            self.type_validator.validate("invalid_type", "value", ValidationTestModel)

    def test_type_validator_field_compatibility(self):
        """Test that type validator checks field type compatibility"""
        # Count should work on any field
        self.assertTrue(self.type_validator.validate("count", "name", ValidationTestModel))
        
        # Sum should only work on numeric fields
        self.assertTrue(self.type_validator.validate("sum", "value", ValidationTestModel))
        with self.assertRaises(ValidationError):
            self.type_validator.validate("sum", "name", ValidationTestModel)

    def test_group_validator_valid_groups(self):
        """Test that group validator accepts valid group by fields"""
        self.assertTrue(self.group_validator.validate(["category"], ValidationTestModel))
        self.assertTrue(self.group_validator.validate(["category", "name"], ValidationTestModel))

    def test_group_validator_invalid_groups(self):
        """Test that group validator rejects invalid group by fields"""
        with self.assertRaises(ValidationError):
            self.group_validator.validate(["nonexistent"], ValidationTestModel)
        with self.assertRaises(ValidationError):
            self.group_validator.validate([123], ValidationTestModel)  # Non-string field

    def test_group_validator_empty_groups(self):
        """Test that group validator handles empty group by fields"""
        self.assertTrue(self.group_validator.validate(None, ValidationTestModel))
        self.assertTrue(self.group_validator.validate([], ValidationTestModel))

    def test_full_validation_valid_aggregation(self):
        """Test full validation with valid aggregation configuration"""
        config = {
            "fields": {
                "value": ["sum", "avg"],
                "price": ["min", "max"]
            },
            "group_by": ["category"]
        }
        self.assertTrue(self.validator.validate(config, ValidationTestModel))

    def test_full_validation_invalid_aggregation(self):
        """Test full validation with invalid aggregation configuration"""
        # Invalid field
        with self.assertRaises(ValidationError):
            config = {
                "fields": {
                    "nonexistent": ["sum"]
                }
            }
            self.validator.validate(config, ValidationTestModel)

        # Invalid aggregation type
        with self.assertRaises(ValidationError):
            config = {
                "fields": {
                    "value": ["invalid_type"]
                }
            }
            self.validator.validate(config, ValidationTestModel)

        # Invalid group by
        with self.assertRaises(ValidationError):
            config = {
                "fields": {
                    "value": ["sum"]
                },
                "group_by": ["nonexistent"]
            }
            self.validator.validate(config, ValidationTestModel)

    def test_full_validation_empty_config(self):
        """Test full validation with empty configuration"""
        with self.assertRaises(ValidationError):
            self.validator.validate({}, ValidationTestModel)
        with self.assertRaises(ValidationError):
            self.validator.validate({"fields": {}}, ValidationTestModel) 