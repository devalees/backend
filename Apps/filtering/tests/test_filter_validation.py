import pytest
from django.db import models
from datetime import datetime, date, time
from ..filters import (
    BaseFilter,
    TextFilter,
    NumericFilter,
    DateFilter,
    TimeFilter,
    BooleanFilter,
    ChoiceFilter,
    RelatedObjectFilter,
    FilterFactory
)
from ..filter_validation import (
    FilterValidationError,
    FieldTypeValidator,
    OperatorValidator,
    ValueValidator,
    FilterValidator
)

class TestFilterValidationError:
    def test_filter_validation_error_message(self):
        """Test that FilterValidationError has correct message"""
        error = FilterValidationError("Test error message")
        assert str(error) == "Test error message"

class TestFieldTypeValidator:
    def test_validate_text_field_type(self):
        """Test that FieldTypeValidator validates text field type correctly"""
        validator = FieldTypeValidator()
        assert validator.validate("name", "char") is True
        assert validator.validate("description", "text") is True
        assert validator.validate("email", "email") is True
        assert validator.validate("url", "url") is True
    
    def test_validate_numeric_field_type(self):
        """Test that FieldTypeValidator validates numeric field type correctly"""
        validator = FieldTypeValidator()
        assert validator.validate("age", "integer") is True
        assert validator.validate("price", "decimal") is True
        assert validator.validate("score", "float") is True
    
    def test_validate_date_field_type(self):
        """Test that FieldTypeValidator validates date field type correctly"""
        validator = FieldTypeValidator()
        assert validator.validate("created_at", "date") is True
        assert validator.validate("updated_at", "datetime") is True
        assert validator.validate("time", "time") is True
    
    def test_validate_boolean_field_type(self):
        """Test that FieldTypeValidator validates boolean field type correctly"""
        validator = FieldTypeValidator()
        assert validator.validate("is_active", "boolean") is True
    
    def test_validate_choice_field_type(self):
        """Test that FieldTypeValidator validates choice field type correctly"""
        validator = FieldTypeValidator()
        assert validator.validate("status", "choice") is True
    
    def test_validate_related_field_type(self):
        """Test that FieldTypeValidator validates related field type correctly"""
        validator = FieldTypeValidator()
        assert validator.validate("user", "related") is True
        assert validator.validate("category", "related") is True
    
    def test_validate_invalid_field_type(self):
        """Test that FieldTypeValidator raises error for invalid field type"""
        validator = FieldTypeValidator()
        with pytest.raises(FilterValidationError) as excinfo:
            validator.validate("field", "invalid_type")
        assert "Invalid field type" in str(excinfo.value)

class TestOperatorValidator:
    def test_validate_text_operators(self):
        """Test that OperatorValidator validates text operators correctly"""
        validator = OperatorValidator()
        assert validator.validate("char", "contains") is True
        assert validator.validate("text", "startswith") is True
        assert validator.validate("email", "endswith") is True
        assert validator.validate("url", "regex") is True
        assert validator.validate("char", "exact") is True
        assert validator.validate("text", "iexact") is True
        assert validator.validate("email", "in") is True
    
    def test_validate_numeric_operators(self):
        """Test that OperatorValidator validates numeric operators correctly"""
        validator = OperatorValidator()
        assert validator.validate("integer", "exact") is True
        assert validator.validate("decimal", "gt") is True
        assert validator.validate("float", "gte") is True
        assert validator.validate("integer", "lt") is True
        assert validator.validate("decimal", "lte") is True
        assert validator.validate("float", "range") is True
        assert validator.validate("integer", "in") is True
    
    def test_validate_date_operators(self):
        """Test that OperatorValidator validates date operators correctly"""
        validator = OperatorValidator()
        assert validator.validate("date", "exact") is True
        assert validator.validate("datetime", "gt") is True
        assert validator.validate("date", "gte") is True
        assert validator.validate("datetime", "lt") is True
        assert validator.validate("date", "lte") is True
        assert validator.validate("datetime", "range") is True
        assert validator.validate("date", "year") is True
        assert validator.validate("datetime", "month") is True
        assert validator.validate("date", "day") is True
        assert validator.validate("datetime", "week_day") is True
    
    def test_validate_time_operators(self):
        """Test that OperatorValidator validates time operators correctly"""
        validator = OperatorValidator()
        assert validator.validate("time", "exact") is True
        assert validator.validate("time", "gt") is True
        assert validator.validate("time", "gte") is True
        assert validator.validate("time", "lt") is True
        assert validator.validate("time", "lte") is True
        assert validator.validate("time", "hour") is True
        assert validator.validate("time", "minute") is True
        assert validator.validate("time", "second") is True
    
    def test_validate_boolean_operators(self):
        """Test that OperatorValidator validates boolean operators correctly"""
        validator = OperatorValidator()
        assert validator.validate("boolean", "exact") is True
        assert validator.validate("boolean", "isnull") is True
    
    def test_validate_choice_operators(self):
        """Test that OperatorValidator validates choice operators correctly"""
        validator = OperatorValidator()
        assert validator.validate("choice", "exact") is True
        assert validator.validate("choice", "in") is True
    
    def test_validate_related_operators(self):
        """Test that OperatorValidator validates related operators correctly"""
        validator = OperatorValidator()
        assert validator.validate("related", "exact") is True
        assert validator.validate("related", "in") is True
        assert validator.validate("related", "isnull") is True
    
    def test_validate_invalid_operator(self):
        """Test that OperatorValidator raises error for invalid operator"""
        validator = OperatorValidator()
        with pytest.raises(FilterValidationError) as excinfo:
            validator.validate("char", "invalid_operator")
        assert "Invalid operator" in str(excinfo.value)

class TestValueValidator:
    def test_validate_text_value(self):
        """Test that ValueValidator validates text values correctly"""
        validator = ValueValidator()
        assert validator.validate("char", "contains", "test") is True
        assert validator.validate("text", "startswith", "test") is True
        assert validator.validate("email", "endswith", "test@example.com") is True
        assert validator.validate("url", "regex", r"^https?://") is True
        assert validator.validate("char", "exact", "test") is True
        assert validator.validate("text", "iexact", "test") is True
        assert validator.validate("email", "in", ["test1", "test2"]) is True
    
    def test_validate_numeric_value(self):
        """Test that ValueValidator validates numeric values correctly"""
        validator = ValueValidator()
        assert validator.validate("integer", "exact", 42) is True
        assert validator.validate("decimal", "gt", 42.5) is True
        assert validator.validate("float", "gte", 42.5) is True
        assert validator.validate("integer", "lt", 42) is True
        assert validator.validate("decimal", "lte", 42.5) is True
        assert validator.validate("float", "range", [42.5, 43.5]) is True
        assert validator.validate("integer", "in", [42, 43, 44]) is True
    
    def test_validate_date_value(self):
        """Test that ValueValidator validates date values correctly"""
        validator = ValueValidator()
        test_date = date(2023, 1, 1)
        test_datetime = datetime(2023, 1, 1, 12, 0)
        
        assert validator.validate("date", "exact", test_date) is True
        assert validator.validate("datetime", "gt", test_datetime) is True
        assert validator.validate("date", "gte", test_date) is True
        assert validator.validate("datetime", "lt", test_datetime) is True
        assert validator.validate("date", "lte", test_date) is True
        assert validator.validate("datetime", "range", [test_datetime, test_datetime]) is True
        assert validator.validate("date", "year", 2023) is True
        assert validator.validate("datetime", "month", 1) is True
        assert validator.validate("date", "day", 1) is True
        assert validator.validate("datetime", "week_day", 1) is True
    
    def test_validate_time_value(self):
        """Test that ValueValidator validates time values correctly"""
        validator = ValueValidator()
        test_time = time(12, 0)
        
        assert validator.validate("time", "exact", test_time) is True
        assert validator.validate("time", "gt", test_time) is True
        assert validator.validate("time", "gte", test_time) is True
        assert validator.validate("time", "lt", test_time) is True
        assert validator.validate("time", "lte", test_time) is True
        assert validator.validate("time", "hour", 12) is True
        assert validator.validate("time", "minute", 0) is True
        assert validator.validate("time", "second", 0) is True
    
    def test_validate_boolean_value(self):
        """Test that ValueValidator validates boolean values correctly"""
        validator = ValueValidator()
        assert validator.validate("boolean", "exact", True) is True
        assert validator.validate("boolean", "exact", False) is True
        assert validator.validate("boolean", "isnull", True) is True
        assert validator.validate("boolean", "isnull", False) is True
    
    def test_validate_choice_value(self):
        """Test that ValueValidator validates choice values correctly"""
        validator = ValueValidator()
        assert validator.validate("choice", "exact", "option1") is True
        assert validator.validate("choice", "in", ["option1", "option2"]) is True
    
    def test_validate_related_value(self):
        """Test that ValueValidator validates related values correctly"""
        validator = ValueValidator()
        assert validator.validate("related", "exact", 1) is True
        assert validator.validate("related", "in", [1, 2, 3]) is True
        assert validator.validate("related", "isnull", True) is True
        assert validator.validate("related", "isnull", False) is True
    
    def test_validate_invalid_value(self):
        """Test that ValueValidator raises error for invalid value"""
        validator = ValueValidator()
        with pytest.raises(FilterValidationError) as excinfo:
            validator.validate("integer", "exact", "not_an_integer")
        assert "Invalid value" in str(excinfo.value)

class TestFilterValidator:
    def test_validate_text_filter(self):
        """Test that FilterValidator validates text filter correctly"""
        validator = FilterValidator()
        filter_data = {
            "field": "name",
            "type": "char",
            "operator": "contains",
            "value": "test"
        }
        assert validator.validate(filter_data) is True
    
    def test_validate_numeric_filter(self):
        """Test that FilterValidator validates numeric filter correctly"""
        validator = FilterValidator()
        filter_data = {
            "field": "age",
            "type": "integer",
            "operator": "gt",
            "value": 18
        }
        assert validator.validate(filter_data) is True
    
    def test_validate_date_filter(self):
        """Test that FilterValidator validates date filter correctly"""
        validator = FilterValidator()
        filter_data = {
            "field": "created_at",
            "type": "date",
            "operator": "gte",
            "value": date(2023, 1, 1)
        }
        assert validator.validate(filter_data) is True
    
    def test_validate_time_filter(self):
        """Test that FilterValidator validates time filter correctly"""
        validator = FilterValidator()
        filter_data = {
            "field": "created_time",
            "type": "time",
            "operator": "exact",
            "value": time(12, 0)
        }
        assert validator.validate(filter_data) is True
    
    def test_validate_boolean_filter(self):
        """Test that FilterValidator validates boolean filter correctly"""
        validator = FilterValidator()
        filter_data = {
            "field": "is_active",
            "type": "boolean",
            "operator": "exact",
            "value": True
        }
        assert validator.validate(filter_data) is True
    
    def test_validate_choice_filter(self):
        """Test that FilterValidator validates choice filter correctly"""
        validator = FilterValidator()
        filter_data = {
            "field": "status",
            "type": "choice",
            "operator": "exact",
            "value": "active"
        }
        assert validator.validate(filter_data) is True
    
    def test_validate_related_filter(self):
        """Test that FilterValidator validates related filter correctly"""
        validator = FilterValidator()
        filter_data = {
            "field": "user",
            "type": "related",
            "operator": "exact",
            "value": 1
        }
        assert validator.validate(filter_data) is True
    
    def test_validate_missing_field(self):
        """Test that FilterValidator raises error for missing field"""
        validator = FilterValidator()
        filter_data = {
            "type": "char",
            "operator": "contains",
            "value": "test"
        }
        with pytest.raises(FilterValidationError) as excinfo:
            validator.validate(filter_data)
        assert "Missing required field" in str(excinfo.value)
    
    def test_validate_missing_type(self):
        """Test that FilterValidator raises error for missing type"""
        validator = FilterValidator()
        filter_data = {
            "field": "name",
            "operator": "contains",
            "value": "test"
        }
        with pytest.raises(FilterValidationError) as excinfo:
            validator.validate(filter_data)
        assert "Missing required field" in str(excinfo.value)
    
    def test_validate_missing_operator(self):
        """Test that FilterValidator raises error for missing operator"""
        validator = FilterValidator()
        filter_data = {
            "field": "name",
            "type": "char",
            "value": "test"
        }
        with pytest.raises(FilterValidationError) as excinfo:
            validator.validate(filter_data)
        assert "Missing required field" in str(excinfo.value)
    
    def test_validate_missing_value(self):
        """Test that FilterValidator raises error for missing value"""
        validator = FilterValidator()
        filter_data = {
            "field": "name",
            "type": "char",
            "operator": "contains"
        }
        with pytest.raises(FilterValidationError) as excinfo:
            validator.validate(filter_data)
        assert "Missing required field" in str(excinfo.value)
    
    def test_validate_invalid_field_type(self):
        """Test that FilterValidator raises error for invalid field type"""
        validator = FilterValidator()
        filter_data = {
            "field": "name",
            "type": "invalid_type",
            "operator": "contains",
            "value": "test"
        }
        with pytest.raises(FilterValidationError) as excinfo:
            validator.validate(filter_data)
        assert "Invalid field type" in str(excinfo.value)
    
    def test_validate_invalid_operator(self):
        """Test that FilterValidator raises error for invalid operator"""
        validator = FilterValidator()
        filter_data = {
            "field": "name",
            "type": "char",
            "operator": "invalid_operator",
            "value": "test"
        }
        with pytest.raises(FilterValidationError) as excinfo:
            validator.validate(filter_data)
        assert "Invalid operator" in str(excinfo.value)
    
    def test_validate_invalid_value(self):
        """Test that FilterValidator raises error for invalid value"""
        validator = FilterValidator()
        filter_data = {
            "field": "age",
            "type": "integer",
            "operator": "exact",
            "value": "not_an_integer"
        }
        with pytest.raises(FilterValidationError) as excinfo:
            validator.validate(filter_data)
        assert "Invalid value" in str(excinfo.value) 