from django.test import TestCase
from django.core.exceptions import ValidationError
from ..models import FieldControl

class FieldControlTests(TestCase):
    def setUp(self):
        self.field_control_data = {
            'field_name': 'username',
            'module_id': 'auth.user',
            'field_type': 'CharField',
            'is_active': True
        }

    def test_field_control_model_exists(self):
        """Test that the FieldControl model exists and has the expected fields"""
        fields = FieldControl._meta.get_fields()
        field_names = [field.name for field in fields]
        
        self.assertIn('field_name', field_names)
        self.assertIn('module_id', field_names)
        self.assertIn('field_type', field_names)
        self.assertIn('is_active', field_names)
        self.assertIn('created_at', field_names)
        self.assertIn('updated_at', field_names)

    def test_field_control_str_method(self):
        """Test the string representation of FieldControl"""
        field_control = FieldControl.objects.create(**self.field_control_data)
        expected_str = f"{self.field_control_data['field_name']} ({self.field_control_data['module_id']})"
        self.assertEqual(str(field_control), expected_str)

    def test_field_control_get_model(self):
        """Test getting the actual model class"""
        field_control = FieldControl.objects.create(**self.field_control_data)
        model = field_control.get_model()
        self.assertIsNotNone(model)
        self.assertEqual(model.__name__, 'User')

    def test_field_control_validation_invalid_module_id(self):
        """Test validation with invalid module_id"""
        with self.assertRaises(ValidationError):
            field_control = FieldControl(
                field_name='test_field',
                module_id='invalid_format',
                field_type='CharField'
            )
            field_control.clean()

    def test_field_control_validation_nonexistent_model(self):
        """Test validation with nonexistent model"""
        with self.assertRaises(ValidationError):
            field_control = FieldControl(
                field_name='test_field',
                module_id='nonexistent.Model',
                field_type='CharField'
            )
            field_control.clean()

    def test_field_control_validation_nonexistent_field(self):
        """Test validation with nonexistent field"""
        with self.assertRaises(ValidationError):
            field_control = FieldControl(
                field_name='nonexistent_field',
                module_id='auth.user',
                field_type='CharField'
            )
            field_control.clean()

    def test_field_control_unique_constraint(self):
        """Test that field_name and module_id combination is unique"""
        # Create first instance
        FieldControl.objects.create(**self.field_control_data)
        
        # Try to create duplicate
        with self.assertRaises(Exception):
            FieldControl.objects.create(**self.field_control_data)

    def test_field_type_auto_detection(self):
        """Test that field_type is automatically detected"""
        field_control = FieldControl.objects.create(
            field_name='username',
            module_id='auth.user',
            is_active=True
        )
        self.assertEqual(field_control.field_type, 'CharField') 