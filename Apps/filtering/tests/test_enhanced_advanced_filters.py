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

class TestEnhancedAdvancedTextFilter:
    """Tests for enhanced text filters with multiple operators"""
    
    def test_advanced_text_filter_apply_endswith(self):
        """Test that AdvancedTextFilter.apply with endswith operator returns correct Q object"""
        filter_instance = AdvancedTextFilter("name", operator="endswith")
        q_object = filter_instance.apply("test")
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('name__endswith', 'test'))"
    
    def test_advanced_text_filter_apply_iendswith(self):
        """Test that AdvancedTextFilter.apply with iendswith operator returns correct Q object"""
        filter_instance = AdvancedTextFilter("name", operator="iendswith")
        q_object = filter_instance.apply("test")
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('name__iendswith', 'test'))"
    
    def test_advanced_text_filter_apply_regex(self):
        """Test that AdvancedTextFilter.apply with regex operator returns correct Q object"""
        filter_instance = AdvancedTextFilter("name", operator="regex")
        q_object = filter_instance.apply("^test.*")
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('name__regex', '^test.*'))"
    
    def test_advanced_text_filter_apply_iregex(self):
        """Test that AdvancedTextFilter.apply with iregex operator returns correct Q object"""
        filter_instance = AdvancedTextFilter("name", operator="iregex")
        q_object = filter_instance.apply("^test.*")
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('name__iregex', '^test.*'))"
    
    def test_advanced_text_filter_apply_regex_invalid_pattern(self):
        """Test that AdvancedTextFilter.apply with regex operator validates pattern"""
        filter_instance = AdvancedTextFilter("name", operator="regex")
        
        with pytest.raises(ValueError):
            filter_instance.apply("[invalid regex")

class TestEnhancedAdvancedNumericFilter:
    """Tests for enhanced numeric filters with comparison operators"""
    
    def test_advanced_numeric_filter_apply_gte(self):
        """Test that AdvancedNumericFilter.apply with gte operator returns correct Q object"""
        filter_instance = AdvancedNumericFilter("age", operator="gte")
        q_object = filter_instance.apply(25)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('age__gte', 25))"
    
    def test_advanced_numeric_filter_apply_lt(self):
        """Test that AdvancedNumericFilter.apply with lt operator returns correct Q object"""
        filter_instance = AdvancedNumericFilter("age", operator="lt")
        q_object = filter_instance.apply(25)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('age__lt', 25))"
    
    def test_advanced_numeric_filter_apply_lte(self):
        """Test that AdvancedNumericFilter.apply with lte operator returns correct Q object"""
        filter_instance = AdvancedNumericFilter("age", operator="lte")
        q_object = filter_instance.apply(25)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('age__lte', 25))"
    
    def test_advanced_numeric_filter_apply_in_with_non_numeric_values(self):
        """Test that AdvancedNumericFilter.apply with in operator validates all values"""
        filter_instance = AdvancedNumericFilter("age", operator="in")
        
        with pytest.raises(ValueError):
            filter_instance.apply([25, "30", 35])

class TestEnhancedAdvancedDateFilter:
    """Tests for enhanced date filters with date-specific operators"""
    
    def test_advanced_date_filter_apply_month(self):
        """Test that AdvancedDateFilter.apply with month operator returns correct Q object"""
        filter_instance = AdvancedDateFilter("created_at", operator="month")
        q_object = filter_instance.apply(1)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_at__month', 1))"
    
    def test_advanced_date_filter_apply_day(self):
        """Test that AdvancedDateFilter.apply with day operator returns correct Q object"""
        filter_instance = AdvancedDateFilter("created_at", operator="day")
        q_object = filter_instance.apply(15)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_at__day', 15))"
    
    def test_advanced_date_filter_apply_week_day(self):
        """Test that AdvancedDateFilter.apply with week_day operator returns correct Q object"""
        filter_instance = AdvancedDateFilter("created_at", operator="week_day")
        q_object = filter_instance.apply(1)  # Monday
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_at__week_day', 1))"
    
    def test_advanced_date_filter_apply_invalid_month_value(self):
        """Test that AdvancedDateFilter.apply with month operator validates value"""
        filter_instance = AdvancedDateFilter("created_at", operator="month")
        
        with pytest.raises(ValueError):
            filter_instance.apply(13)  # Invalid month
        
        with pytest.raises(ValueError):
            filter_instance.apply(0)  # Invalid month
    
    def test_advanced_date_filter_apply_invalid_day_value(self):
        """Test that AdvancedDateFilter.apply with day operator validates value"""
        filter_instance = AdvancedDateFilter("created_at", operator="day")
        
        with pytest.raises(ValueError):
            filter_instance.apply(32)  # Invalid day
        
        with pytest.raises(ValueError):
            filter_instance.apply(0)  # Invalid day
    
    def test_advanced_date_filter_apply_invalid_week_day_value(self):
        """Test that AdvancedDateFilter.apply with week_day operator validates value"""
        filter_instance = AdvancedDateFilter("created_at", operator="week_day")
        
        with pytest.raises(ValueError):
            filter_instance.apply(8)  # Invalid week day
        
        with pytest.raises(ValueError):
            filter_instance.apply(0)  # Invalid week day

class TestEnhancedAdvancedTimeFilter:
    """Tests for enhanced time filters with time-specific operators"""
    
    def test_advanced_time_filter_apply_minute(self):
        """Test that AdvancedTimeFilter.apply with minute operator returns correct Q object"""
        filter_instance = AdvancedTimeFilter("created_time", operator="minute")
        q_object = filter_instance.apply(30)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_time__minute', 30))"
    
    def test_advanced_time_filter_apply_second(self):
        """Test that AdvancedTimeFilter.apply with second operator returns correct Q object"""
        filter_instance = AdvancedTimeFilter("created_time", operator="second")
        q_object = filter_instance.apply(45)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_time__second', 45))"
    
    def test_advanced_time_filter_apply_invalid_hour_value(self):
        """Test that AdvancedTimeFilter.apply with hour operator validates value"""
        filter_instance = AdvancedTimeFilter("created_time", operator="hour")
        
        with pytest.raises(ValueError):
            filter_instance.apply(24)  # Invalid hour
        
        with pytest.raises(ValueError):
            filter_instance.apply(-1)  # Invalid hour
    
    def test_advanced_time_filter_apply_invalid_minute_value(self):
        """Test that AdvancedTimeFilter.apply with minute operator validates value"""
        filter_instance = AdvancedTimeFilter("created_time", operator="minute")
        
        with pytest.raises(ValueError):
            filter_instance.apply(60)  # Invalid minute
        
        with pytest.raises(ValueError):
            filter_instance.apply(-1)  # Invalid minute
    
    def test_advanced_time_filter_apply_invalid_second_value(self):
        """Test that AdvancedTimeFilter.apply with second operator validates value"""
        filter_instance = AdvancedTimeFilter("created_time", operator="second")
        
        with pytest.raises(ValueError):
            filter_instance.apply(60)  # Invalid second
        
        with pytest.raises(ValueError):
            filter_instance.apply(-1)  # Invalid second

class TestEnhancedAdvancedBooleanFilter:
    """Tests for enhanced boolean filters with null checks"""
    
    def test_advanced_boolean_filter_apply_isnull_true(self):
        """Test that AdvancedBooleanFilter.apply with isnull operator and True returns correct Q object"""
        filter_instance = AdvancedBooleanFilter("is_active", operator="isnull")
        q_object = filter_instance.apply(True)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('is_active__isnull', True))"
    
    def test_advanced_boolean_filter_apply_isnull_false(self):
        """Test that AdvancedBooleanFilter.apply with isnull operator and False returns correct Q object"""
        filter_instance = AdvancedBooleanFilter("is_active", operator="isnull")
        q_object = filter_instance.apply(False)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('is_active__isnull', False))"
    
    def test_advanced_boolean_filter_apply_isnull_invalid_value(self):
        """Test that AdvancedBooleanFilter.apply with isnull operator validates value"""
        filter_instance = AdvancedBooleanFilter("is_active", operator="isnull")
        
        with pytest.raises(ValueError):
            filter_instance.apply("true")

class TestEnhancedAdvancedChoiceFilter:
    """Tests for enhanced choice filters with multiple selection"""
    
    def test_advanced_choice_filter_apply_in_with_multiple_values(self):
        """Test that AdvancedChoiceFilter.apply with in operator and multiple values returns correct Q object"""
        filter_instance = AdvancedChoiceFilter("status", choices=["active", "inactive", "pending"], operator="in")
        q_object = filter_instance.apply(["active", "pending"])
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('status__in', ['active', 'pending']))"
    
    def test_advanced_choice_filter_apply_in_with_invalid_choices(self):
        """Test that AdvancedChoiceFilter.apply with in operator validates all choices"""
        filter_instance = AdvancedChoiceFilter("status", choices=["active", "inactive", "pending"], operator="in")
        
        with pytest.raises(ValueError):
            filter_instance.apply(["active", "invalid"])

class TestEnhancedAdvancedRelatedObjectFilter:
    """Tests for enhanced related object filters with field traversal"""
    
    def test_advanced_related_object_filter_apply_with_field_traversal(self):
        """Test that AdvancedRelatedObjectFilter.apply with field traversal returns correct Q object"""
        filter_instance = AdvancedRelatedObjectFilter("user", related_field="profile__bio", operator="contains")
        q_object = filter_instance.apply("developer")
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('user__profile__bio__contains', 'developer'))"
    
    def test_advanced_related_object_filter_apply_with_deep_field_traversal(self):
        """Test that AdvancedRelatedObjectFilter.apply with deep field traversal returns correct Q object"""
        filter_instance = AdvancedRelatedObjectFilter("project", related_field="team__leader__email", operator="endswith")
        q_object = filter_instance.apply("@example.com")
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('project__team__leader__email__endswith', '@example.com'))"
    
    def test_advanced_related_object_filter_apply_with_related_field_and_in_operator(self):
        """Test that AdvancedRelatedObjectFilter.apply with related field and in operator returns correct Q object"""
        filter_instance = AdvancedRelatedObjectFilter("project", related_field="team__role", operator="in")
        q_object = filter_instance.apply(["developer", "designer"])
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('project__team__role__in', ['developer', 'designer']))"
    
    def test_advanced_related_object_filter_apply_with_related_field_and_isnull_operator(self):
        """Test that AdvancedRelatedObjectFilter.apply with related field and isnull operator returns correct Q object"""
        filter_instance = AdvancedRelatedObjectFilter("project", related_field="team__leader", operator="isnull")
        q_object = filter_instance.apply(True)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('project__team__leader__isnull', True))" 