import pytest
import pandas as pd
import csv
from io import StringIO, BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth import get_user_model
from Apps.data_transfer.models import TestModel

User = get_user_model()

class TestDataTransfer(TestCase):
    def setUp(self):
        self.test_data = [
            {'name': 'John Doe', 'email': 'john@example.com', 'age': 30},
            {'name': 'Jane Smith', 'email': 'jane@example.com', 'age': 25},
        ]
        self.csv_content = "name,email,age\nJohn Doe,john@example.com,30\nJane Smith,jane@example.com,25"
        excel_buffer = BytesIO()
        pd.DataFrame(self.test_data).to_excel(excel_buffer, index=False)
        self.excel_content = excel_buffer.getvalue()

    def test_csv_import(self):
        """Test importing data from CSV file"""
        from Apps.data_transfer.transfer import DataTransfer
        csv_file = SimpleUploadedFile(
            "test.csv",
            self.csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        transfer = DataTransfer(TestModel)
        result = transfer.import_csv(csv_file)
        self.assertEqual(len(result), 2)
        self.assertEqual(TestModel.objects.count(), 2)
        self.assertEqual(TestModel.objects.first().name, 'John Doe')

    def test_excel_import(self):
        """Test importing data from Excel file"""
        from Apps.data_transfer.transfer import DataTransfer
        excel_file = SimpleUploadedFile(
            "test.xlsx",
            self.excel_content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        transfer = DataTransfer(TestModel)
        result = transfer.import_excel(excel_file)
        self.assertEqual(len(result), 2)
        self.assertEqual(TestModel.objects.count(), 2)
        self.assertEqual(TestModel.objects.first().name, 'John Doe')

    def test_csv_export(self):
        """Test exporting data to CSV file"""
        from Apps.data_transfer.transfer import DataTransfer
        # Create test data
        for data in self.test_data:
            TestModel.objects.create(**data)
        
        transfer = DataTransfer(TestModel)
        csv_output = transfer.export_csv()
        
        # Read the CSV output
        csv_data = csv.DictReader(StringIO(csv_output))
        exported_data = list(csv_data)
        
        self.assertEqual(len(exported_data), 2)
        self.assertEqual(exported_data[0]['name'], 'John Doe')
        self.assertEqual(exported_data[1]['name'], 'Jane Smith')

    def test_excel_export(self):
        """Test exporting data to Excel file"""
        from Apps.data_transfer.transfer import DataTransfer
        # Create test data
        for data in self.test_data:
            TestModel.objects.create(**data)
        
        transfer = DataTransfer(TestModel)
        excel_output = transfer.export_excel()
        
        # Read the Excel output
        df = pd.read_excel(BytesIO(excel_output))
        self.assertEqual(len(df), 2)
        self.assertEqual(df.iloc[0]['name'], 'John Doe')
        self.assertEqual(df.iloc[1]['name'], 'Jane Smith')

    def test_invalid_csv_import(self):
        """Test importing invalid CSV data"""
        from Apps.data_transfer.transfer import DataTransfer
        invalid_csv = "name,email,age\nJohn Doe,invalid-email,30"
        csv_file = SimpleUploadedFile(
            "test.csv",
            invalid_csv.encode('utf-8'),
            content_type="text/csv"
        )
        transfer = DataTransfer(TestModel)
        with self.assertRaises(ValueError):
            transfer.import_csv(csv_file)

    def test_invalid_excel_import(self):
        """Test importing invalid Excel data"""
        from Apps.data_transfer.transfer import DataTransfer
        invalid_data = pd.DataFrame([
            {'name': 'John Doe', 'email': 'invalid-email', 'age': 30}
        ])
        excel_buffer = BytesIO()
        invalid_data.to_excel(excel_buffer, index=False)
        excel_file = SimpleUploadedFile(
            "test.xlsx",
            excel_buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        transfer = DataTransfer(TestModel)
        with self.assertRaises(ValueError):
            transfer.import_excel(excel_file)

    def test_empty_file_import(self):
        """Test importing empty files"""
        from Apps.data_transfer.transfer import DataTransfer
        empty_csv = SimpleUploadedFile(
            "empty.csv",
            b"",
            content_type="text/csv"
        )
        empty_excel = SimpleUploadedFile(
            "empty.xlsx",
            b"",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        transfer = DataTransfer(TestModel)
        
        with self.assertRaises(ValueError):
            transfer.import_csv(empty_csv)
        
        with self.assertRaises(ValueError):
            transfer.import_excel(empty_excel)

    def test_export_empty_queryset(self):
        """Test exporting when no data exists"""
        from Apps.data_transfer.transfer import DataTransfer
        transfer = DataTransfer(TestModel)
        
        csv_output = transfer.export_csv()
        self.assertEqual(csv_output, "")
        
        excel_output = transfer.export_excel()
        self.assertEqual(excel_output, b"")

    def test_custom_field_mapping(self):
        """Test custom field mapping during import/export"""
        from Apps.data_transfer.transfer import DataTransfer
        custom_mapping = {
            'full_name': 'name',
            'email_address': 'email',
            'user_age': 'age'
        }
    
        # Test import with custom mapping
        csv_content = "full_name,email_address,user_age\nJohn Doe,john@example.com,30"
        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content.encode('utf-8'),
            content_type="text/csv"
        )
        transfer = DataTransfer(TestModel, field_mapping=custom_mapping)
        result = transfer.import_csv(csv_file)
        self.assertEqual(len(result), 1)
        self.assertEqual(TestModel.objects.first().name, 'John Doe')
    
        # Test export with custom mapping
        excel_output = transfer.export_excel()
        df = pd.read_excel(BytesIO(excel_output))
        # Check that all custom mapped fields are present
        expected_columns = ['full_name', 'email_address', 'user_age']
        for col in expected_columns:
            self.assertIn(col, df.columns)
        # Check that created_by is present (it's a required field)
        self.assertIn('created_by', df.columns)

    def test_validation_rules(self):
        """Test custom validation rules during import"""
        from Apps.data_transfer.transfer import DataTransfer
        
        def validate_age(value):
            try:
                age = int(value)
                if age < 0 or age > 150:
                    raise ValueError("Age must be between 0 and 150")
                return age
            except (TypeError, ValueError):
                raise ValueError("Age must be a valid integer")
        
        validation_rules = {
            'age': validate_age
        }
        
        transfer = DataTransfer(TestModel, validation_rules=validation_rules)
        
        # Test valid data
        valid_csv = "name,email,age\nJohn Doe,john@example.com,30"
        csv_file = SimpleUploadedFile(
            "test.csv",
            valid_csv.encode('utf-8'),
            content_type="text/csv"
        )
        result = transfer.import_csv(csv_file)
        self.assertEqual(len(result), 1)
        self.assertEqual(TestModel.objects.first().age, 30)
        
        # Test invalid data
        invalid_csv = "name,email,age\nJohn Doe,john@example.com,200"
        csv_file = SimpleUploadedFile(
            "test.csv",
            invalid_csv.encode('utf-8'),
            content_type="text/csv"
        )
        with self.assertRaises(ValueError):
            transfer.import_csv(csv_file) 