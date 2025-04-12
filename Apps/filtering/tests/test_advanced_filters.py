import pytest
from django.db.models import Q
from datetime import datetime, date, time
from ..advanced_filters import (
    AdvancedTextFilter,
    AdvancedNumericFilter,
    AdvancedDateFilter,
    AdvancedTimeFilter,
    AdvancedBooleanFilter,
    AdvancedChoiceFilter,
    AdvancedRelatedObjectFilter,
    AdvancedFilterFactory
)

class TestAdvancedTextFilter:
    def test_advanced_text_filter_initialization(self):
        """Test that AdvancedTextFilter initializes correctly with valid operator"""
        filter_instance = AdvancedTextFilter("name", operator="exact")
        assert filter_instance.field_name == "name"
        assert filter_instance.operator == "exact"
    
    def test_advanced_text_filter_initialization_invalid_operator(self):
        """Test that AdvancedTextFilter raises ValueError with invalid operator"""
        with pytest.raises(ValueError):
            AdvancedTextFilter("name", operator="invalid_operator")
    
    def test_advanced_text_filter_apply_exact(self):
        """Test that AdvancedTextFilter.apply with exact operator returns correct Q object"""
        filter_instance = AdvancedTextFilter("name", operator="exact")
        q_object = filter_instance.apply("test")
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('name', 'test'))"
    
    def test_advanced_text_filter_apply_icontains(self):
        """Test that AdvancedTextFilter.apply with icontains operator returns correct Q object"""
        filter_instance = AdvancedTextFilter("name", operator="icontains")
        q_object = filter_instance.apply("test")
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('name__icontains', 'test'))"
    
    def test_advanced_text_filter_apply_startswith(self):
        """Test that AdvancedTextFilter.apply with startswith operator returns correct Q object"""
        filter_instance = AdvancedTextFilter("name", operator="startswith")
        q_object = filter_instance.apply("test")
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('name__startswith', 'test'))"
    
    def test_advanced_text_filter_apply_invalid_value(self):
        """Test that AdvancedTextFilter.apply raises ValueError with invalid value"""
        filter_instance = AdvancedTextFilter("name", operator="exact")
        
        with pytest.raises(ValueError):
            filter_instance.apply(123)

class TestAdvancedNumericFilter:
    def test_advanced_numeric_filter_initialization(self):
        """Test that AdvancedNumericFilter initializes correctly with valid operator"""
        filter_instance = AdvancedNumericFilter("age", operator="exact")
        assert filter_instance.field_name == "age"
        assert filter_instance.operator == "exact"
    
    def test_advanced_numeric_filter_initialization_invalid_operator(self):
        """Test that AdvancedNumericFilter raises ValueError with invalid operator"""
        with pytest.raises(ValueError):
            AdvancedNumericFilter("age", operator="invalid_operator")
    
    def test_advanced_numeric_filter_apply_exact(self):
        """Test that AdvancedNumericFilter.apply with exact operator returns correct Q object"""
        filter_instance = AdvancedNumericFilter("age", operator="exact")
        q_object = filter_instance.apply(25)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('age', 25))"
    
    def test_advanced_numeric_filter_apply_gt(self):
        """Test that AdvancedNumericFilter.apply with gt operator returns correct Q object"""
        filter_instance = AdvancedNumericFilter("age", operator="gt")
        q_object = filter_instance.apply(25)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('age__gt', 25))"
    
    def test_advanced_numeric_filter_apply_in(self):
        """Test that AdvancedNumericFilter.apply with in operator returns correct Q object"""
        filter_instance = AdvancedNumericFilter("age", operator="in")
        q_object = filter_instance.apply([25, 30, 35])
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('age__in', [25, 30, 35]))"
    
    def test_advanced_numeric_filter_apply_range(self):
        """Test that AdvancedNumericFilter.apply with range operator returns correct Q object"""
        filter_instance = AdvancedNumericFilter("age", operator="range")
        q_object = filter_instance.apply([25, 35])
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('age__range', [25, 35]))"
    
    def test_advanced_numeric_filter_apply_invalid_value(self):
        """Test that AdvancedNumericFilter.apply raises ValueError with invalid value"""
        filter_instance = AdvancedNumericFilter("age", operator="exact")
        
        with pytest.raises(ValueError):
            filter_instance.apply("25")
    
    def test_advanced_numeric_filter_apply_invalid_in_value(self):
        """Test that AdvancedNumericFilter.apply raises ValueError with invalid in value"""
        filter_instance = AdvancedNumericFilter("age", operator="in")
        
        with pytest.raises(ValueError):
            filter_instance.apply(25)
    
    def test_advanced_numeric_filter_apply_invalid_range_value(self):
        """Test that AdvancedNumericFilter.apply raises ValueError with invalid range value"""
        filter_instance = AdvancedNumericFilter("age", operator="range")
        
        with pytest.raises(ValueError):
            filter_instance.apply([25])
        
        with pytest.raises(ValueError):
            filter_instance.apply([25, 30, 35])

class TestAdvancedDateFilter:
    def test_advanced_date_filter_initialization(self):
        """Test that AdvancedDateFilter initializes correctly with valid operator"""
        filter_instance = AdvancedDateFilter("created_at", operator="exact")
        assert filter_instance.field_name == "created_at"
        assert filter_instance.operator == "exact"
    
    def test_advanced_date_filter_initialization_invalid_operator(self):
        """Test that AdvancedDateFilter raises ValueError with invalid operator"""
        with pytest.raises(ValueError):
            AdvancedDateFilter("created_at", operator="invalid_operator")
    
    def test_advanced_date_filter_apply_exact(self):
        """Test that AdvancedDateFilter.apply with exact operator returns correct Q object"""
        filter_instance = AdvancedDateFilter("created_at", operator="exact")
        test_date = date(2023, 1, 1)
        q_object = filter_instance.apply(test_date)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_at', datetime.date(2023, 1, 1)))"
    
    def test_advanced_date_filter_apply_gt(self):
        """Test that AdvancedDateFilter.apply with gt operator returns correct Q object"""
        filter_instance = AdvancedDateFilter("created_at", operator="gt")
        test_date = date(2023, 1, 1)
        q_object = filter_instance.apply(test_date)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_at__gt', datetime.date(2023, 1, 1)))"
    
    def test_advanced_date_filter_apply_year(self):
        """Test that AdvancedDateFilter.apply with year operator returns correct Q object"""
        filter_instance = AdvancedDateFilter("created_at", operator="year")
        q_object = filter_instance.apply(2023)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_at__year', 2023))"
    
    def test_advanced_date_filter_apply_range(self):
        """Test that AdvancedDateFilter.apply with range operator returns correct Q object"""
        filter_instance = AdvancedDateFilter("created_at", operator="range")
        test_dates = [date(2023, 1, 1), date(2023, 12, 31)]
        q_object = filter_instance.apply(test_dates)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_at__range', [datetime.date(2023, 1, 1), datetime.date(2023, 12, 31)]))"
    
    def test_advanced_date_filter_apply_invalid_value(self):
        """Test that AdvancedDateFilter.apply raises ValueError with invalid value"""
        filter_instance = AdvancedDateFilter("created_at", operator="exact")
        
        with pytest.raises(ValueError):
            filter_instance.apply("2023-01-01")
    
    def test_advanced_date_filter_apply_invalid_year_value(self):
        """Test that AdvancedDateFilter.apply raises ValueError with invalid year value"""
        filter_instance = AdvancedDateFilter("created_at", operator="year")
        
        with pytest.raises(ValueError):
            filter_instance.apply("2023")
    
    def test_advanced_date_filter_apply_invalid_range_value(self):
        """Test that AdvancedDateFilter.apply raises ValueError with invalid range value"""
        filter_instance = AdvancedDateFilter("created_at", operator="range")
        
        with pytest.raises(ValueError):
            filter_instance.apply([date(2023, 1, 1)])
        
        with pytest.raises(ValueError):
            filter_instance.apply([date(2023, 1, 1), date(2023, 12, 31), date(2024, 1, 1)])

class TestAdvancedTimeFilter:
    def test_advanced_time_filter_initialization(self):
        """Test that AdvancedTimeFilter initializes correctly with valid operator"""
        filter_instance = AdvancedTimeFilter("created_time", operator="exact")
        assert filter_instance.field_name == "created_time"
        assert filter_instance.operator == "exact"
    
    def test_advanced_time_filter_initialization_invalid_operator(self):
        """Test that AdvancedTimeFilter raises ValueError with invalid operator"""
        with pytest.raises(ValueError):
            AdvancedTimeFilter("created_time", operator="invalid_operator")
    
    def test_advanced_time_filter_apply_exact(self):
        """Test that AdvancedTimeFilter.apply with exact operator returns correct Q object"""
        filter_instance = AdvancedTimeFilter("created_time", operator="exact")
        test_time = time(12, 0)
        q_object = filter_instance.apply(test_time)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_time', datetime.time(12, 0)))"
    
    def test_advanced_time_filter_apply_gt(self):
        """Test that AdvancedTimeFilter.apply with gt operator returns correct Q object"""
        filter_instance = AdvancedTimeFilter("created_time", operator="gt")
        test_time = time(12, 0)
        q_object = filter_instance.apply(test_time)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_time__gt', datetime.time(12, 0)))"
    
    def test_advanced_time_filter_apply_hour(self):
        """Test that AdvancedTimeFilter.apply with hour operator returns correct Q object"""
        filter_instance = AdvancedTimeFilter("created_time", operator="hour")
        q_object = filter_instance.apply(12)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_time__hour', 12))"
    
    def test_advanced_time_filter_apply_range(self):
        """Test that AdvancedTimeFilter.apply with range operator returns correct Q object"""
        filter_instance = AdvancedTimeFilter("created_time", operator="range")
        test_times = [time(9, 0), time(17, 0)]
        q_object = filter_instance.apply(test_times)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_time__range', [datetime.time(9, 0), datetime.time(17, 0)]))"
    
    def test_advanced_time_filter_apply_invalid_value(self):
        """Test that AdvancedTimeFilter.apply raises ValueError with invalid value"""
        filter_instance = AdvancedTimeFilter("created_time", operator="exact")
        
        with pytest.raises(ValueError):
            filter_instance.apply("12:00")
    
    def test_advanced_time_filter_apply_invalid_hour_value(self):
        """Test that AdvancedTimeFilter.apply raises ValueError with invalid hour value"""
        filter_instance = AdvancedTimeFilter("created_time", operator="hour")
        
        with pytest.raises(ValueError):
            filter_instance.apply("12")
    
    def test_advanced_time_filter_apply_invalid_range_value(self):
        """Test that AdvancedTimeFilter.apply raises ValueError with invalid range value"""
        filter_instance = AdvancedTimeFilter("created_time", operator="range")
        
        with pytest.raises(ValueError):
            filter_instance.apply([time(9, 0)])
        
        with pytest.raises(ValueError):
            filter_instance.apply([time(9, 0), time(12, 0), time(17, 0)])

class TestAdvancedBooleanFilter:
    def test_advanced_boolean_filter_initialization(self):
        """Test that AdvancedBooleanFilter initializes correctly with valid operator"""
        filter_instance = AdvancedBooleanFilter("is_active", operator="exact")
        assert filter_instance.field_name == "is_active"
        assert filter_instance.operator == "exact"
    
    def test_advanced_boolean_filter_initialization_invalid_operator(self):
        """Test that AdvancedBooleanFilter raises ValueError with invalid operator"""
        with pytest.raises(ValueError):
            AdvancedBooleanFilter("is_active", operator="invalid_operator")
    
    def test_advanced_boolean_filter_apply_exact(self):
        """Test that AdvancedBooleanFilter.apply with exact operator returns correct Q object"""
        filter_instance = AdvancedBooleanFilter("is_active", operator="exact")
        q_object = filter_instance.apply(True)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('is_active', True))"
    
    def test_advanced_boolean_filter_apply_isnull(self):
        """Test that AdvancedBooleanFilter.apply with isnull operator returns correct Q object"""
        filter_instance = AdvancedBooleanFilter("is_active", operator="isnull")
        q_object = filter_instance.apply(True)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('is_active__isnull', True))"
    
    def test_advanced_boolean_filter_apply_invalid_value(self):
        """Test that AdvancedBooleanFilter.apply raises ValueError with invalid value"""
        filter_instance = AdvancedBooleanFilter("is_active", operator="exact")
        
        with pytest.raises(ValueError):
            filter_instance.apply(1)

class TestAdvancedChoiceFilter:
    def test_advanced_choice_filter_initialization(self):
        """Test that AdvancedChoiceFilter initializes correctly with valid operator"""
        choices = ["option1", "option2"]
        filter_instance = AdvancedChoiceFilter("status", choices=choices, operator="exact")
        assert filter_instance.field_name == "status"
        assert filter_instance.operator == "exact"
        assert filter_instance.choices == choices
    
    def test_advanced_choice_filter_initialization_invalid_operator(self):
        """Test that AdvancedChoiceFilter raises ValueError with invalid operator"""
        choices = ["option1", "option2"]
        
        with pytest.raises(ValueError):
            AdvancedChoiceFilter("status", choices=choices, operator="invalid_operator")
    
    def test_advanced_choice_filter_apply_exact(self):
        """Test that AdvancedChoiceFilter.apply with exact operator returns correct Q object"""
        choices = ["option1", "option2"]
        filter_instance = AdvancedChoiceFilter("status", choices=choices, operator="exact")
        q_object = filter_instance.apply("option1")
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('status', 'option1'))"
    
    def test_advanced_choice_filter_apply_in(self):
        """Test that AdvancedChoiceFilter.apply with in operator returns correct Q object"""
        choices = ["option1", "option2", "option3"]
        filter_instance = AdvancedChoiceFilter("status", choices=choices, operator="in")
        q_object = filter_instance.apply(["option1", "option2"])
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('status__in', ['option1', 'option2']))"
    
    def test_advanced_choice_filter_apply_invalid_value(self):
        """Test that AdvancedChoiceFilter.apply raises ValueError with invalid value"""
        choices = ["option1", "option2"]
        filter_instance = AdvancedChoiceFilter("status", choices=choices, operator="exact")
        
        with pytest.raises(ValueError):
            filter_instance.apply("option3")
    
    def test_advanced_choice_filter_apply_invalid_in_value(self):
        """Test that AdvancedChoiceFilter.apply raises ValueError with invalid in value"""
        choices = ["option1", "option2"]
        filter_instance = AdvancedChoiceFilter("status", choices=choices, operator="in")
        
        with pytest.raises(ValueError):
            filter_instance.apply("option1")
        
        with pytest.raises(ValueError):
            filter_instance.apply(["option1", "option3"])

class TestAdvancedRelatedObjectFilter:
    def test_advanced_related_object_filter_initialization(self):
        """Test that AdvancedRelatedObjectFilter initializes correctly with valid operator"""
        filter_instance = AdvancedRelatedObjectFilter("user", related_field="id", operator="exact")
        assert filter_instance.field_name == "user"
        assert filter_instance.related_field == "id"
        assert filter_instance.operator == "exact"
    
    def test_advanced_related_object_filter_initialization_invalid_operator(self):
        """Test that AdvancedRelatedObjectFilter raises ValueError with invalid operator"""
        with pytest.raises(ValueError):
            AdvancedRelatedObjectFilter("user", related_field="id", operator="invalid_operator")
    
    def test_advanced_related_object_filter_apply_exact_without_related_field(self):
        """Test that AdvancedRelatedObjectFilter.apply with exact operator returns correct Q object without related field"""
        filter_instance = AdvancedRelatedObjectFilter("user", operator="exact")
        q_object = filter_instance.apply(1)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('user', 1))"
    
    def test_advanced_related_object_filter_apply_exact_with_related_field(self):
        """Test that AdvancedRelatedObjectFilter.apply with exact operator returns correct Q object with related field"""
        filter_instance = AdvancedRelatedObjectFilter("user", related_field="id", operator="exact")
        q_object = filter_instance.apply(1)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('user__id', 1))"
    
    def test_advanced_related_object_filter_apply_in(self):
        """Test that AdvancedRelatedObjectFilter.apply with in operator returns correct Q object"""
        filter_instance = AdvancedRelatedObjectFilter("user", related_field="id", operator="in")
        q_object = filter_instance.apply([1, 2, 3])
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('user__id__in', [1, 2, 3]))"
    
    def test_advanced_related_object_filter_apply_isnull(self):
        """Test that AdvancedRelatedObjectFilter.apply with isnull operator returns correct Q object"""
        filter_instance = AdvancedRelatedObjectFilter("user", related_field="id", operator="isnull")
        q_object = filter_instance.apply(True)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('user__id__isnull', True))"
    
    def test_advanced_related_object_filter_apply_invalid_in_value(self):
        """Test that AdvancedRelatedObjectFilter.apply raises ValueError with invalid in value"""
        filter_instance = AdvancedRelatedObjectFilter("user", related_field="id", operator="in")
        
        with pytest.raises(ValueError):
            filter_instance.apply(1)

class TestAdvancedFilterFactory:
    def test_advanced_filter_factory_create_text_filter(self):
        """Test that AdvancedFilterFactory.create_filter creates correct AdvancedTextFilter"""
        filter_instance = AdvancedFilterFactory.create_filter("name", "char")
        
        assert isinstance(filter_instance, AdvancedTextFilter)
        assert filter_instance.field_name == "name"
        assert filter_instance.operator == "icontains"
    
    def test_advanced_filter_factory_create_text_filter_with_operator(self):
        """Test that AdvancedFilterFactory.create_filter creates correct AdvancedTextFilter with operator"""
        filter_instance = AdvancedFilterFactory.create_filter("name", "char", operator="exact")
        
        assert isinstance(filter_instance, AdvancedTextFilter)
        assert filter_instance.field_name == "name"
        assert filter_instance.operator == "exact"
    
    def test_advanced_filter_factory_create_numeric_filter(self):
        """Test that AdvancedFilterFactory.create_filter creates correct AdvancedNumericFilter"""
        filter_instance = AdvancedFilterFactory.create_filter("age", "integer")
        
        assert isinstance(filter_instance, AdvancedNumericFilter)
        assert filter_instance.field_name == "age"
        assert filter_instance.operator == "exact"
    
    def test_advanced_filter_factory_create_date_filter(self):
        """Test that AdvancedFilterFactory.create_filter creates correct AdvancedDateFilter"""
        filter_instance = AdvancedFilterFactory.create_filter("created_at", "date")
        
        assert isinstance(filter_instance, AdvancedDateFilter)
        assert filter_instance.field_name == "created_at"
        assert filter_instance.operator == "exact"
    
    def test_advanced_filter_factory_create_time_filter(self):
        """Test that AdvancedFilterFactory.create_filter creates correct AdvancedTimeFilter"""
        filter_instance = AdvancedFilterFactory.create_filter("created_time", "time")
        
        assert isinstance(filter_instance, AdvancedTimeFilter)
        assert filter_instance.field_name == "created_time"
        assert filter_instance.operator == "exact"
    
    def test_advanced_filter_factory_create_boolean_filter(self):
        """Test that AdvancedFilterFactory.create_filter creates correct AdvancedBooleanFilter"""
        filter_instance = AdvancedFilterFactory.create_filter("is_active", "boolean")
        
        assert isinstance(filter_instance, AdvancedBooleanFilter)
        assert filter_instance.field_name == "is_active"
        assert filter_instance.operator == "exact"
    
    def test_advanced_filter_factory_create_choice_filter(self):
        """Test that AdvancedFilterFactory.create_filter creates correct AdvancedChoiceFilter with choices"""
        choices = ["option1", "option2"]
        filter_instance = AdvancedFilterFactory.create_filter("status", "choice", choices=choices)
        
        assert isinstance(filter_instance, AdvancedChoiceFilter)
        assert filter_instance.field_name == "status"
        assert filter_instance.choices == choices
        assert filter_instance.operator == "exact"
    
    def test_advanced_filter_factory_create_unsupported_filter(self):
        """Test that AdvancedFilterFactory.create_filter raises ValueError for unsupported types"""
        with pytest.raises(ValueError):
            AdvancedFilterFactory.create_filter("field", "unsupported_type") 