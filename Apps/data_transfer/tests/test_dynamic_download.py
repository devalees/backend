from django.test import TestCase, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from Apps.contact.models import Contact, ContactCategory
import pandas as pd
import json
from io import BytesIO
import os

User = get_user_model()

class TestDynamicDownloadMixin(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = ContactCategory.objects.create(
            name="Test Category",
            description="Test Description",
            created_by=self.user
        )
        
        # Create test contact
        contact = Contact(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            category=self.category,
            created_by=self.user
        )
        contact.skip_validation = True
        contact.save()
        self.contact = contact
        
        # Create test files
        self.csv_content = b"first_name,last_name,email,phone\nJane,Doe,jane@example.com,0987654321"
        self.excel_content = pd.DataFrame({
            'first_name': ['Jane'],
            'last_name': ['Doe'],
            'email': ['jane@example.com'],
            'phone': ['0987654321']
        })
        
        # Create test files
        self.csv_file = SimpleUploadedFile(
            "test.csv",
            self.csv_content,
            content_type="text/csv"
        )
        
        excel_buffer = BytesIO()
        self.excel_content.to_excel(excel_buffer, index=False)
        self.excel_file = SimpleUploadedFile(
            "test.xlsx",
            excel_buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_get_exportable_fields(self):
        """Test getting exportable fields"""
        fields = self.contact.get_exportable_fields()
        
        # Check that required fields are included
        self.assertIn('first_name', fields)
        self.assertIn('last_name', fields)
        self.assertIn('email', fields)
        self.assertIn('phone', fields)
        
        # Check that excluded fields are not included
        self.assertNotIn('id', fields)
        self.assertNotIn('created_at', fields)
        self.assertNotIn('updated_at', fields)

    def test_get_field_verbose_names(self):
        """Test getting verbose names for fields"""
        verbose_names = self.contact.get_field_verbose_names()
        
        # Check that field names are properly mapped
        self.assertEqual(verbose_names['first_name'], 'First Name')
        self.assertEqual(verbose_names['last_name'], 'Last Name')
        self.assertEqual(verbose_names['email'], 'Email')
        self.assertEqual(verbose_names['phone'], 'Phone')

    def test_to_dict(self):
        """Test converting model instance to dictionary"""
        data = self.contact.to_dict()
        
        # Check that all fields are properly converted
        self.assertEqual(data['first_name'], 'John')
        self.assertEqual(data['last_name'], 'Doe')
        self.assertEqual(data['email'], 'john@example.com')
        self.assertEqual(data['phone'], '+1234567890')
        self.assertEqual(data['category'], str(self.category))

    def test_download_as_excel(self):
        """Test downloading data as Excel"""
        response = Contact.download_as_excel()
        
        # Check response properties
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response['Content-Type'], Contact.ALLOWED_EXTENSIONS['xlsx'])
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename="contact_'))
        self.assertTrue(response['Content-Disposition'].endswith('.xlsx"'))
        
        # Read the Excel content and verify data
        df = pd.read_excel(BytesIO(response.content))
        self.assertEqual(len(df), 1)  # One record
        self.assertEqual(df.iloc[0]['First Name'], 'John')
        self.assertEqual(df.iloc[0]['Last Name'], 'Doe')

    def test_download_as_csv(self):
        """Test downloading data as CSV"""
        response = Contact.download_as_csv()
        
        # Check response properties
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response['Content-Type'], Contact.ALLOWED_EXTENSIONS['csv'])
        self.assertTrue(response['Content-Disposition'].startswith('attachment; filename="contact_'))
        self.assertTrue(response['Content-Disposition'].endswith('.csv"'))
        
        # Read the CSV content and verify data
        df = pd.read_csv(BytesIO(response.content))
        self.assertEqual(len(df), 1)  # One record
        self.assertEqual(df.iloc[0]['First Name'], 'John')
        self.assertEqual(df.iloc[0]['Last Name'], 'Doe')

    def test_validate_file_type(self):
        """Test file type validation"""
        # Test valid file types
        self.assertTrue(Contact.validate_file_type(self.csv_file))
        self.assertTrue(Contact.validate_file_type(self.excel_file))
        
        # Test invalid file type
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"invalid content",
            content_type="text/plain"
        )
        with self.assertRaises(ValidationError):
            Contact.validate_file_type(invalid_file)
        
        # Test no file
        with self.assertRaises(ValidationError):
            Contact.validate_file_type(None)

    def test_import_data_csv(self):
        """Test importing data from CSV"""
        initial_count = Contact.objects.count()
        imported_count = Contact.import_data(self.csv_file)
        
        # Check that one record was imported
        self.assertEqual(imported_count, 1)
        self.assertEqual(Contact.objects.count(), initial_count + 1)
        
        # Verify imported data
        imported_contact = Contact.objects.latest('id')
        self.assertEqual(imported_contact.first_name, 'Jane')
        self.assertEqual(imported_contact.last_name, 'Doe')
        self.assertEqual(imported_contact.email, 'jane@example.com')
        self.assertEqual(imported_contact.phone, '+0987654321')

    def test_import_data_excel(self):
        """Test importing data from Excel"""
        initial_count = Contact.objects.count()
        imported_count = Contact.import_data(self.excel_file)
        
        # Check that one record was imported
        self.assertEqual(imported_count, 1)
        self.assertEqual(Contact.objects.count(), initial_count + 1)
        
        # Verify imported data
        imported_contact = Contact.objects.latest('id')
        self.assertEqual(imported_contact.first_name, 'Jane')
        self.assertEqual(imported_contact.last_name, 'Doe')
        self.assertEqual(imported_contact.email, 'jane@example.com')
        self.assertEqual(imported_contact.phone, '+0987654321')

    def test_import_data_invalid_format(self):
        """Test importing data with invalid format"""
        invalid_csv = SimpleUploadedFile(
            "test.csv",
            b"invalid,format\ndata,here",
            content_type="text/csv"
        )
        
        with self.assertRaises(ValidationError):
            Contact.import_data(invalid_csv)

    def test_queryset_filtering(self):
        """Test downloading filtered queryset"""
        # Create another contact
        contact = Contact(
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            phone="0987654321",
            category=self.category,
            created_by=self.user
        )
        contact.skip_validation = True
        contact.save()
        
        # Filter queryset
        queryset = Contact.objects.filter(first_name="John")
        
        # Download filtered data
        response = Contact.download_as_excel(queryset=queryset)
        
        # Verify that only filtered data is included
        df = pd.read_excel(BytesIO(response.content))
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['First Name'], 'John')

    def tearDown(self):
        """Clean up test files"""
        if hasattr(self, 'csv_file'):
            self.csv_file.close()
        if hasattr(self, 'excel_file'):
            self.excel_file.close() 