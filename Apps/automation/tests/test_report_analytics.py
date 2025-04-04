from django.test import TestCase
from django.utils import timezone
import pytz
from datetime import timedelta, datetime
from Apps.automation.models import ReportTemplate, Report, ReportSchedule, ReportAnalytics
from Apps.users.models import User

class ReportAnalyticsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.template = ReportTemplate.objects.create(
            name='Test Template',
            description='Test Description',
            query={
                'model': 'Task',
                'filters': {'status': 'completed'},
                'aggregations': [
                    {'type': 'count', 'field': '*'}
                ]
            },
            format='pdf',
            created_by=self.user
        )
        
    def test_report_generation_metrics(self):
        """Test tracking of report generation metrics"""
        now = timezone.now()
        # Create multiple reports with different statuses
        report1 = Report.objects.create(
            template=self.template,
            parameters={
                'start_date': now.isoformat(),
                'end_date': (now + timedelta(days=7)).isoformat()
            },
            created_by=self.user
        )
        report2 = Report.objects.create(
            template=self.template,
            parameters={
                'start_date': now.isoformat(),
                'end_date': (now + timedelta(days=7)).isoformat()
            },
            created_by=self.user
        )
        
        # Update report statuses
        report1.complete_generation('/path/to/report1.pdf')
        report2.fail_generation('Test error message')
        
        # Calculate metrics
        analytics = ReportAnalytics.calculate_metrics(self.template)
        
        self.assertEqual(analytics.total_reports, 2)
        self.assertEqual(analytics.successful_reports, 1)
        self.assertEqual(analytics.failed_reports, 1)
        self.assertEqual(analytics.success_rate, 50.0)

    def test_report_schedule_metrics(self):
        """Test tracking of schedule execution metrics"""
        now = timezone.now()
        schedule = ReportSchedule.objects.create(
            name='Test Schedule',
            template=self.template,
            schedule={'frequency': 'daily', 'time': '09:00'},
            parameters={
                'start_date': now.isoformat(),
                'end_date': (now + timedelta(days=7)).isoformat()
            },
            created_by=self.user
        )
        
        # Create reports for this schedule
        for _ in range(3):
            report = Report.objects.create(
                template=self.template,
                parameters=schedule.parameters,
                created_by=self.user
            )
            report.complete_generation(f'/path/to/report_{report.id}.pdf')
        
        # Calculate schedule metrics
        analytics = ReportAnalytics.calculate_schedule_metrics(schedule)
        
        self.assertEqual(analytics.total_executions, 3)
        self.assertEqual(analytics.successful_executions, 3)
        self.assertEqual(analytics.execution_success_rate, 100.0)

    def test_report_usage_patterns(self):
        """Test analysis of report usage patterns"""
        # Create reports with fixed dates
        today = timezone.make_aware(datetime(2025, 4, 4))
        yesterday = timezone.make_aware(datetime(2025, 4, 3))
        
        # Today's reports
        for _ in range(3):
            report = Report.objects.create(
                template=self.template,
                parameters={
                    'start_date': today.isoformat(),
                    'end_date': (today + timedelta(days=7)).isoformat()
                },
                created_by=self.user
            )
            report.complete_generation(f'/path/to/report_{_}.pdf')
            # Update created_at directly in the database
            Report.objects.filter(id=report.id).update(created_at=today)
        
        # Yesterday's reports
        for _ in range(2):
            report = Report.objects.create(
                template=self.template,
                parameters={
                    'start_date': yesterday.isoformat(),
                    'end_date': (yesterday + timedelta(days=7)).isoformat()
                },
                created_by=self.user
            )
            report.complete_generation(f'/path/to/report_{_}.pdf')
            # Update created_at directly in the database
            Report.objects.filter(id=report.id).update(created_at=yesterday)
        
        # Calculate usage patterns
        analytics = ReportAnalytics.calculate_usage_patterns(self.template)
        
        self.assertEqual(analytics.daily_average, 2.5)  # (3 + 2) / 2 days
        self.assertEqual(analytics.peak_usage_day, today.date())
        self.assertEqual(analytics.peak_daily_count, 3)

    def test_performance_metrics(self):
        """Test tracking of report generation performance"""
        now = timezone.now()
        report = Report.objects.create(
            template=self.template,
            parameters={
                'start_date': now.isoformat(),
                'end_date': (now + timedelta(days=7)).isoformat()
            },
            created_by=self.user
        )
        
        # Simulate report generation with timing
        start_time = timezone.now()
        report.start_generation()
        
        # Simulate some processing time
        end_time = start_time + timedelta(seconds=5)
        report.complete_generation('/path/to/report.pdf', 5.0)
        
        # Calculate performance metrics
        analytics = ReportAnalytics.calculate_metrics(self.template)
        
        self.assertGreater(analytics.average_generation_time, 0)
        self.assertEqual(analytics.min_generation_time, 5.0)
        self.assertEqual(analytics.max_generation_time, 5.0) 