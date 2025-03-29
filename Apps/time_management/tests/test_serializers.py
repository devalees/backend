import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from Apps.time_management.serializers import (
    TimeCategorySerializer, TimeEntrySerializer, TimesheetSerializer,
    TimesheetEntrySerializer, WorkScheduleSerializer
)
from .factories import (
    UserFactory, ProjectFactory, TimeCategoryFactory, TimeEntryFactory,
    TimesheetFactory, TimesheetEntryFactory, WorkScheduleFactory
)

User = get_user_model()

@pytest.mark.django_db
class TestTimeCategorySerializer:
    def test_serialize_time_category(self):
        category = TimeCategoryFactory()
        serializer = TimeCategorySerializer(category)
        data = serializer.data
        assert data['id'] == category.id
        assert data['name'] == category.name
        assert data['description'] == category.description
        assert data['is_billable'] == category.is_billable
        assert 'created_by' in data

    def test_deserialize_time_category(self):
        user = UserFactory()
        data = {
            'name': 'Test Category',
            'description': 'Test Description',
            'is_billable': True
        }
        serializer = TimeCategorySerializer(data=data, partial=True)
        assert serializer.is_valid()
        category = serializer.save(created_by=user)
        assert category.name == data['name']
        assert category.description == data['description']
        assert category.is_billable == data['is_billable']
        assert category.created_by == user

@pytest.mark.django_db
class TestTimeEntrySerializer:
    def test_serialize_time_entry(self):
        entry = TimeEntryFactory()
        serializer = TimeEntrySerializer(entry)
        data = serializer.data
        assert data['id'] == entry.id
        assert data['user'] == entry.user.id
        assert data['project'] == entry.project.id
        assert data['category'] == entry.category.id
        assert data['description'] == entry.description
        assert data['start_time'] is not None
        assert data['end_time'] is not None
        assert data['hours'] == entry.hours
        assert data['is_billable'] == entry.is_billable

    def test_deserialize_time_entry(self):
        user = UserFactory()
        project = ProjectFactory()
        category = TimeCategoryFactory()
        data = {
            'project': project.id,
            'category': category.id,
            'description': 'Test Entry',
            'start_time': timezone.now(),
            'end_time': timezone.now() + timezone.timedelta(hours=2),
            'is_billable': True
        }
        serializer = TimeEntrySerializer(data=data, partial=True)
        assert serializer.is_valid()
        entry = serializer.save(user=user)
        assert entry.project == project
        assert entry.category == category
        assert entry.description == data['description']
        assert entry.is_billable == data['is_billable']
        assert entry.user == user

    def test_validate_time_entry(self):
        data = {
            'start_time': timezone.now() + timezone.timedelta(hours=2),
            'end_time': timezone.now()
        }
        serializer = TimeEntrySerializer(data=data, partial=True)
        assert not serializer.is_valid()
        assert 'end_time' in serializer.errors

@pytest.mark.django_db
class TestTimesheetSerializer:
    def test_serialize_timesheet(self):
        timesheet = TimesheetFactory()
        serializer = TimesheetSerializer(timesheet)
        data = serializer.data
        assert data['id'] == timesheet.id
        assert data['user'] == timesheet.user.id
        assert data['start_date'] is not None
        assert data['end_date'] is not None
        assert data['status'] == timesheet.status
        assert data['notes'] == timesheet.notes
        assert 'total_hours' in data

    def test_deserialize_timesheet(self):
        user = UserFactory()
        data = {
            'user': user.id,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() + timezone.timedelta(days=7),
            'status': 'draft',
            'notes': 'Test Notes'
        }
        serializer = TimesheetSerializer(data=data)
        assert serializer.is_valid()
        timesheet = serializer.save()
        assert timesheet.start_date == data['start_date']
        assert timesheet.end_date == data['end_date']
        assert timesheet.status == data['status']
        assert timesheet.notes == data['notes']
        assert timesheet.user == user

    def test_validate_timesheet_dates(self):
        user = UserFactory()
        data = {
            'user': user.id,
            'start_date': timezone.now().date() + timezone.timedelta(days=7),
            'end_date': timezone.now().date()
        }
        serializer = TimesheetSerializer(data=data)
        assert not serializer.is_valid()
        assert 'end_date' in serializer.errors

@pytest.mark.django_db
class TestTimesheetEntrySerializer:
    def test_serialize_timesheet_entry(self):
        entry = TimesheetEntryFactory()
        serializer = TimesheetEntrySerializer(entry)
        data = serializer.data
        assert data['id'] == entry.id
        assert data['timesheet'] == entry.timesheet.id
        assert data['date'] is not None
        assert data['hours'] == entry.hours
        assert data['category'] == entry.category.id
        assert data['description'] == entry.description

    def test_deserialize_timesheet_entry(self):
        timesheet = TimesheetFactory()
        time_entry = TimeEntryFactory()
        category = TimeCategoryFactory()
        data = {
            'timesheet': timesheet.id,
            'time_entry': time_entry.id,
            'date': timezone.now().date(),
            'hours': 8.0,
            'category': category.id,
            'description': 'Test Entry'
        }
        serializer = TimesheetEntrySerializer(data=data)
        assert serializer.is_valid()
        entry = serializer.save()
        assert entry.timesheet == timesheet
        assert entry.time_entry == time_entry
        assert entry.hours == data['hours']
        assert entry.description == data['description']

    def test_validate_timesheet_entry_hours(self):
        data = {
            'hours': -1
        }
        serializer = TimesheetEntrySerializer(data=data, partial=True)
        assert not serializer.is_valid()
        assert 'hours' in serializer.errors

@pytest.mark.django_db
class TestWorkScheduleSerializer:
    def test_serialize_work_schedule(self):
        schedule = WorkScheduleFactory()
        serializer = WorkScheduleSerializer(schedule)
        data = serializer.data
        assert data['id'] == schedule.id
        assert data['user'] == schedule.user.id
        assert data['name'] == schedule.name
        assert data['start_time'] is not None
        assert data['end_time'] is not None
        assert data['days_of_week'] == schedule.days_of_week
        assert data['is_active'] == schedule.is_active

    def test_deserialize_work_schedule(self):
        user = UserFactory()
        data = {
            'user': user.id,
            'name': 'Test Schedule',
            'start_time': '09:00:00',
            'end_time': '17:00:00',
            'days_of_week': [0, 1, 2],  # Monday, Tuesday, Wednesday
            'is_active': True
        }
        serializer = WorkScheduleSerializer(data=data, partial=True)
        valid = serializer.is_valid()
        if not valid:
            print("\nValidation errors:", serializer.errors)
            print("\nValidation data:", data)
            print("\nUser ID:", user.id)
        assert valid
        schedule = serializer.save()
        assert schedule.name == data['name']
        assert str(schedule.start_time) == data['start_time']
        assert str(schedule.end_time) == data['end_time']
        assert schedule.days_of_week == data['days_of_week']
        assert schedule.is_active == data['is_active']
        assert schedule.user == user

    def test_validate_work_schedule_times(self):
        data = {
            'start_time': '17:00:00',
            'end_time': '09:00:00'
        }
        serializer = WorkScheduleSerializer(data=data, partial=True)
        assert not serializer.is_valid()
        assert 'end_time' in serializer.errors 