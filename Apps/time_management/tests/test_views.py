import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from Apps.time_management.models import TimeCategory
from Apps.time_management.tests.factories import (
    UserFactory, ProjectFactory, TimeCategoryFactory, TimeEntryFactory,
    TimesheetFactory, TimesheetEntryFactory, WorkScheduleFactory
)

User = get_user_model()

@pytest.mark.django_db
class TestTimeCategoryViewSet(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('time-category-list')

    def test_list_time_categories(self):
        # Delete any existing categories
        TimeCategory.objects.all().delete()
        # Create new categories
        TimeCategoryFactory.create_batch(3)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_time_category(self):
        data = {
            'name': 'Test Category',
            'description': 'Test Description',
            'is_billable': True
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == data['name']
        assert response.data['created_by'] == self.user.id

    def test_retrieve_time_category(self):
        category = TimeCategoryFactory()
        url = reverse('time-category-detail', kwargs={'pk': category.pk})
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == category.id

    def test_update_time_category(self):
        category = TimeCategoryFactory()
        url = reverse('time-category-detail', kwargs={'pk': category.pk})
        data = {'name': 'Updated Category'}
        response = self.client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == data['name']

    def test_delete_time_category(self):
        category = TimeCategoryFactory()
        url = reverse('time-category-detail', kwargs={'pk': category.pk})
        response = self.client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

@pytest.mark.django_db
class TestTimeEntryViewSet(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('time-entry-list')

    def test_list_time_entries(self):
        TimeEntryFactory.create_batch(3, user=self.user)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_time_entry(self):
        project = ProjectFactory()
        category = TimeCategoryFactory()
        start_time = timezone.now()
        end_time = start_time + timezone.timedelta(hours=2)
        hours = 2.0  # 2 hours difference between start_time and end_time
        data = {
            'user': self.user.id,
            'project': project.id,
            'category': category.id,
            'description': 'Test Entry',
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'hours': hours,
            'is_billable': True
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user'] == self.user.id

    def test_time_entry_summary(self):
        TimeEntryFactory.create_batch(3, user=self.user, is_billable=True)
        TimeEntryFactory.create_batch(2, user=self.user, is_billable=False)
        url = reverse('time-entry-summary')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['billable_hours'] > 0
        assert response.data['non_billable_hours'] > 0

    def test_filter_time_entries(self):
        project = ProjectFactory()
        TimeEntryFactory.create_batch(2, user=self.user, project=project)
        response = self.client.get(f"{self.url}?project_id={project.id}")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

@pytest.mark.django_db
class TestTimesheetViewSet(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('timesheet-list')

    def test_list_timesheets(self):
        TimesheetFactory.create_batch(3, user=self.user)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_timesheet(self):
        # Delete any existing timesheets for this user
        self.user.timesheet_set.all().delete()
        
        start_date = timezone.now().date()
        end_date = start_date + timezone.timedelta(days=7)
        data = {
            'user': self.user.id,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'status': 'draft',
            'notes': 'Test Notes',
            'total_hours': 0.00
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user'] == self.user.id

    def test_submit_timesheet(self):
        timesheet = TimesheetFactory(user=self.user, status='draft')
        url = reverse('timesheet-submit', kwargs={'pk': timesheet.pk})
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        timesheet.refresh_from_db()
        assert timesheet.status == 'submitted'

    def test_approve_timesheet(self):
        timesheet = TimesheetFactory(user=self.user, status='submitted')
        url = reverse('timesheet-approve', kwargs={'pk': timesheet.pk})
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        timesheet.refresh_from_db()
        assert timesheet.status == 'approved'

    def test_reject_timesheet(self):
        timesheet = TimesheetFactory(user=self.user, status='submitted')
        url = reverse('timesheet-reject', kwargs={'pk': timesheet.pk})
        response = self.client.post(url)
        assert response.status_code == status.HTTP_200_OK
        timesheet.refresh_from_db()
        assert timesheet.status == 'rejected'

@pytest.mark.django_db
class TestTimesheetEntryViewSet(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('timesheet-entry-list')

    def test_list_timesheet_entries(self):
        timesheet = TimesheetFactory(user=self.user)
        TimesheetEntryFactory.create_batch(3, timesheet=timesheet)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_timesheet_entry(self):
        timesheet = TimesheetFactory(user=self.user, status='draft')
        time_entry = TimeEntryFactory(user=self.user)
        category = TimeCategoryFactory()
        data = {
            'timesheet': timesheet.id,
            'time_entry': time_entry.id,
            'date': timezone.now().date().isoformat(),
            'hours': 8.0,
            'category': category.id,
            'description': 'Test Entry'
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_entry_in_submitted_timesheet(self):
        timesheet = TimesheetFactory(user=self.user, status='submitted')
        category = TimeCategoryFactory()
        data = {
            'timesheet': timesheet.id,
            'date': timezone.now().date(),
            'hours': 8.0,
            'category': category.id,
            'description': 'Test Entry'
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestWorkScheduleViewSet(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = reverse('work-schedule-list')

    def test_list_work_schedules(self):
        WorkScheduleFactory.create_batch(3, user=self.user)
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 3

    def test_create_work_schedule(self):
        data = {
            'user': self.user.id,
            'start_time': '09:00',
            'end_time': '17:00',
            'days_of_week': [0, 1, 2],  # Monday, Tuesday, Wednesday
            'is_active': True
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['user'] == self.user.id

    def test_get_current_schedule(self):
        WorkScheduleFactory(user=self.user, is_active=True)
        url = reverse('work-schedule-current')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is True
