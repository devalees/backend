from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from Apps.automation.models import Report, ReportTemplate, ReportSchedule
from .factories import UserFactory

class ReportTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.template_data = {
            'name': 'Test Report Template',
            'description': 'A test report template',
            'query': {
                'model': 'Task',
                'filters': {'status': 'completed'},
                'aggregations': [
                    {'type': 'count', 'field': '*'},
                    {'type': 'avg', 'field': 'duration'}
                ]
            },
            'format': 'pdf',
            'created_by': self.user
        }
        self.report_data = {
            'name': 'Test Report',
            'template': None,  # Will be set after template creation
            'parameters': {
                'start_date': timezone.now().isoformat(),
                'end_date': timezone.now().isoformat()
            },
            'created_by': self.user
        }

    def test_create_report_template(self):
        """Test creating a report template with valid data"""
        template = ReportTemplate.objects.create(**self.template_data)
        self.assertEqual(template.name, self.template_data['name'])
        self.assertEqual(template.query, self.template_data['query'])
        self.assertEqual(template.format, self.template_data['format'])

    def test_create_report_template_invalid_query(self):
        """Test creating a report template with invalid query structure"""
        invalid_data = self.template_data.copy()
        invalid_data['query'] = {'invalid': 'structure'}
        
        with self.assertRaises(ValidationError):
            ReportTemplate.objects.create(**invalid_data)

    def test_create_report(self):
        """Test creating a report from a template"""
        template = ReportTemplate.objects.create(**self.template_data)
        self.report_data['template'] = template
        
        report = Report.objects.create(**self.report_data)
        self.assertEqual(report.name, self.report_data['name'])
        self.assertEqual(report.template, template)
        self.assertEqual(report.parameters, self.report_data['parameters'])

    def test_create_report_schedule(self):
        """Test scheduling a report with valid schedule parameters"""
        template = ReportTemplate.objects.create(**self.template_data)
        schedule_data = {
            'template': template,
            'name': 'Daily Report',
            'schedule': {
                'frequency': 'daily',
                'time': '09:00',
                'timezone': 'UTC'
            },
            'parameters': self.report_data['parameters'],
            'created_by': self.user
        }
        
        schedule = ReportSchedule.objects.create(**schedule_data)
        self.assertEqual(schedule.name, schedule_data['name'])
        self.assertEqual(schedule.schedule['frequency'], 'daily')
        self.assertTrue(schedule.is_active)

    def test_validate_report_parameters(self):
        """Test validation of report parameters against template requirements"""
        template = ReportTemplate.objects.create(**self.template_data)
        self.report_data['template'] = template
        
        # Test with missing required parameter
        invalid_params = {'start_date': timezone.now().isoformat()}
        self.report_data['parameters'] = invalid_params
        
        with self.assertRaises(ValidationError):
            Report.objects.create(**self.report_data)

    def test_report_status_tracking(self):
        """Test report generation status tracking"""
        template = ReportTemplate.objects.create(**self.template_data)
        self.report_data['template'] = template
        
        report = Report.objects.create(**self.report_data)
        self.assertEqual(report.status, 'pending')
        
        report.start_generation()
        self.assertEqual(report.status, 'generating')
        
        report.complete_generation('path/to/report.pdf')
        self.assertEqual(report.status, 'completed')
        self.assertIsNotNone(report.generated_at)
        self.assertEqual(report.output_path, 'path/to/report.pdf')

    def test_report_error_handling(self):
        """Test error handling during report generation"""
        template = ReportTemplate.objects.create(**self.template_data)
        self.report_data['template'] = template
        
        report = Report.objects.create(**self.report_data)
        error_message = "Failed to generate report: Database error"
        
        report.fail_generation(error_message)
        self.assertEqual(report.status, 'failed')
        self.assertEqual(report.error_message, error_message) 