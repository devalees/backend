import pytest
from django.db.models import Q
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

class TestBaseFilter:
    def test_base_filter_abstract_methods(self):
        """Test that BaseFilter abstract methods raise NotImplementedError"""
        class ConcreteFilter(BaseFilter):
            pass
        
        filter_instance = ConcreteFilter("test_field")
        
        with pytest.raises(NotImplementedError):
            filter_instance.apply("test_value")
        
        with pytest.raises(NotImplementedError):
            filter_instance.validate("test_value")

class TestTextFilter:
    def test_text_filter_apply(self):
        """Test that TextFilter.apply returns correct Q object"""
        filter_instance = TextFilter("name")
        q_object = filter_instance.apply("test")
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('name__icontains', 'test'))"
    
    def test_text_filter_validate(self):
        """Test that TextFilter.validate correctly validates string values"""
        filter_instance = TextFilter("name")
        
        assert filter_instance.validate("test") is True
        assert filter_instance.validate(123) is False
        assert filter_instance.validate(None) is False

class TestNumericFilter:
    def test_numeric_filter_apply(self):
        """Test that NumericFilter.apply returns correct Q object"""
        filter_instance = NumericFilter("age")
        q_object = filter_instance.apply(25)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('age', 25))"
    
    def test_numeric_filter_validate(self):
        """Test that NumericFilter.validate correctly validates numeric values"""
        filter_instance = NumericFilter("age")
        
        assert filter_instance.validate(25) is True
        assert filter_instance.validate(25.5) is True
        assert filter_instance.validate("25") is False
        assert filter_instance.validate(None) is False

class TestDateFilter:
    def test_date_filter_apply(self):
        """Test that DateFilter.apply returns correct Q object"""
        filter_instance = DateFilter("created_at")
        test_date = date(2023, 1, 1)
        q_object = filter_instance.apply(test_date)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_at', datetime.date(2023, 1, 1)))"
    
    def test_date_filter_validate(self):
        """Test that DateFilter.validate correctly validates date values"""
        filter_instance = DateFilter("created_at")
        
        assert filter_instance.validate(date(2023, 1, 1)) is True
        assert filter_instance.validate(datetime(2023, 1, 1, 12, 0)) is True
        assert filter_instance.validate("2023-01-01") is False
        assert filter_instance.validate(None) is False

class TestTimeFilter:
    def test_time_filter_apply(self):
        """Test that TimeFilter.apply returns correct Q object"""
        filter_instance = TimeFilter("created_time")
        test_time = time(12, 0)
        q_object = filter_instance.apply(test_time)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('created_time', datetime.time(12, 0)))"
    
    def test_time_filter_validate(self):
        """Test that TimeFilter.validate correctly validates time values"""
        filter_instance = TimeFilter("created_time")
        
        assert filter_instance.validate(time(12, 0)) is True
        assert filter_instance.validate("12:00") is False
        assert filter_instance.validate(None) is False

class TestBooleanFilter:
    def test_boolean_filter_apply(self):
        """Test that BooleanFilter.apply returns correct Q object"""
        filter_instance = BooleanFilter("is_active")
        q_object = filter_instance.apply(True)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('is_active', True))"
    
    def test_boolean_filter_validate(self):
        """Test that BooleanFilter.validate correctly validates boolean values"""
        filter_instance = BooleanFilter("is_active")
        
        assert filter_instance.validate(True) is True
        assert filter_instance.validate(False) is True
        assert filter_instance.validate(1) is False
        assert filter_instance.validate("true") is False
        assert filter_instance.validate(None) is False

class TestChoiceFilter:
    def test_choice_filter_apply(self):
        """Test that ChoiceFilter.apply returns correct Q object"""
        choices = ["option1", "option2", "option3"]
        filter_instance = ChoiceFilter("status", choices=choices)
        q_object = filter_instance.apply("option1")
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('status', 'option1'))"
    
    def test_choice_filter_validate(self):
        """Test that ChoiceFilter.validate correctly validates choice values"""
        choices = ["option1", "option2", "option3"]
        filter_instance = ChoiceFilter("status", choices=choices)
        
        assert filter_instance.validate("option1") is True
        assert filter_instance.validate("option2") is True
        assert filter_instance.validate("option3") is True
        assert filter_instance.validate("option4") is False
        assert filter_instance.validate(None) is False

class TestRelatedObjectFilter:
    def test_related_object_filter_apply_without_related_field(self):
        """Test that RelatedObjectFilter.apply returns correct Q object without related field"""
        filter_instance = RelatedObjectFilter("user")
        q_object = filter_instance.apply(1)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('user', 1))"
    
    def test_related_object_filter_apply_with_related_field(self):
        """Test that RelatedObjectFilter.apply returns correct Q object with related field"""
        filter_instance = RelatedObjectFilter("user", related_field="id")
        q_object = filter_instance.apply(1)
        
        assert isinstance(q_object, Q)
        assert str(q_object) == "(AND: ('user__id', 1))"
    
    def test_related_object_filter_validate(self):
        """Test that RelatedObjectFilter.validate correctly validates values"""
        filter_instance = RelatedObjectFilter("user")
        
        assert filter_instance.validate(1) is True
        assert filter_instance.validate("test") is True
        assert filter_instance.validate(None) is False

class TestFilterFactory:
    def test_filter_factory_create_text_filter(self):
        """Test that FilterFactory.create_filter creates correct TextFilter"""
        filter_instance = FilterFactory.create_filter("name", "char")
        
        assert isinstance(filter_instance, TextFilter)
        assert filter_instance.field_name == "name"
    
    def test_filter_factory_create_numeric_filter(self):
        """Test that FilterFactory.create_filter creates correct NumericFilter"""
        filter_instance = FilterFactory.create_filter("age", "integer")
        
        assert isinstance(filter_instance, NumericFilter)
        assert filter_instance.field_name == "age"
    
    def test_filter_factory_create_date_filter(self):
        """Test that FilterFactory.create_filter creates correct DateFilter"""
        filter_instance = FilterFactory.create_filter("created_at", "date")
        
        assert isinstance(filter_instance, DateFilter)
        assert filter_instance.field_name == "created_at"
    
    def test_filter_factory_create_time_filter(self):
        """Test that FilterFactory.create_filter creates correct TimeFilter"""
        filter_instance = FilterFactory.create_filter("created_time", "time")
        
        assert isinstance(filter_instance, TimeFilter)
        assert filter_instance.field_name == "created_time"
    
    def test_filter_factory_create_boolean_filter(self):
        """Test that FilterFactory.create_filter creates correct BooleanFilter"""
        filter_instance = FilterFactory.create_filter("is_active", "boolean")
        
        assert isinstance(filter_instance, BooleanFilter)
        assert filter_instance.field_name == "is_active"
    
    def test_filter_factory_create_choice_filter(self):
        """Test that FilterFactory.create_filter creates correct ChoiceFilter with choices"""
        choices = ["option1", "option2"]
        filter_instance = FilterFactory.create_filter("status", "choice", choices=choices)
        
        assert isinstance(filter_instance, ChoiceFilter)
        assert filter_instance.field_name == "status"
        assert filter_instance.choices == choices
    
    def test_filter_factory_create_unsupported_filter(self):
        """Test that FilterFactory.create_filter raises ValueError for unsupported types"""
        with pytest.raises(ValueError):
            FilterFactory.create_filter("field", "unsupported_type") 