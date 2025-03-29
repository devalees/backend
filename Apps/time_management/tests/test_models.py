import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import time
from ..models import TimeCategory, TimeEntry, Timesheet, TimesheetEntry, WorkSchedule
from .factories import (
    TimeCategoryFactory, TimeEntryFactory, TimesheetFactory,
    TimesheetEntryFactory, WorkScheduleFactory, UserFactory, ProjectFactory
)

User = get_user_model()

@pytest.mark.django_db
class TestTimeCategory:
    def test_create_time_category(self):
        category = TimeCategoryFactory()
        assert category.name is not None
        assert category.description is not None
        assert category.is_billable is not None
        assert category.created_by is not None

    def test_time_category_str(self):
        category = TimeCategoryFactory(name="Test Category")
        assert str(category) == "Test Category"

@pytest.mark.django_db
class TestTimeEntry:
    def test_create_time_entry(self):
        entry = TimeEntryFactory()
        assert entry.user is not None
        assert entry.project is not None
        assert entry.category is not None
        assert entry.start_time is not None
        assert entry.end_time is not None
        assert entry.hours > 0
        assert entry.is_billable is not None

    def test_time_entry_str(self):
        entry = TimeEntryFactory()
        expected = f"{entry.user.username} - {entry.project.title} - {entry.hours} hours"
        assert str(entry) == expected

    def test_time_entry_validation(self):
        with pytest.raises(ValidationError):
            entry = TimeEntryFactory(
                start_time=timezone.now(),
                end_time=timezone.now() - timezone.timedelta(hours=1)
            )
            entry.full_clean()

    def test_time_entry_hours_calculation(self):
        start_time = timezone.now()
        end_time = start_time + timezone.timedelta(hours=2)
        entry = TimeEntryFactory(start_time=start_time, end_time=end_time)
        assert entry.hours == 2.0

@pytest.mark.django_db
class TestTimesheet:
    def test_create_timesheet(self):
        timesheet = TimesheetFactory()
        assert timesheet.user is not None
        assert timesheet.start_date is not None
        assert timesheet.end_date is not None
        assert timesheet.status in ['draft', 'submitted', 'approved', 'rejected']
        assert timesheet.notes is not None

    def test_timesheet_str(self):
        timesheet = TimesheetFactory()
        expected = f"{timesheet.user.username} - {timesheet.start_date} to {timesheet.end_date}"
        assert str(timesheet) == expected

    def test_timesheet_validation(self):
        with pytest.raises(ValidationError):
            timesheet = TimesheetFactory(
                start_date=timezone.now().date(),
                end_date=timezone.now().date() - timezone.timedelta(days=1)
            )
            timesheet.full_clean()

    def test_timesheet_status_transitions(self):
        timesheet = TimesheetFactory(status='draft')
        assert timesheet.submitted_at is None
        assert timesheet.approved_at is None
        assert timesheet.approved_by is None

        timesheet.status = 'submitted'
        timesheet.submitted_at = timezone.now()
        timesheet.save()
        assert timesheet.submitted_at is not None

        timesheet.status = 'approved'
        timesheet.approved_at = timezone.now()
        timesheet.approved_by = UserFactory()
        timesheet.save()
        assert timesheet.approved_at is not None
        assert timesheet.approved_by is not None

@pytest.mark.django_db
class TestTimesheetEntry:
    def test_create_timesheet_entry(self):
        entry = TimesheetEntryFactory()
        assert entry.timesheet is not None
        assert entry.date is not None
        assert entry.hours > 0
        assert entry.category is not None
        assert entry.description is not None

    def test_timesheet_entry_str(self):
        entry = TimesheetEntryFactory()
        expected = f"{entry.timesheet.user.username} - {entry.date} ({entry.hours} hours)"
        assert str(entry) == expected

    def test_timesheet_entry_validation(self):
        with pytest.raises(ValidationError):
            entry = TimesheetEntryFactory(hours=-1)
            entry.full_clean()

@pytest.mark.django_db
class TestWorkSchedule:
    def test_create_work_schedule(self):
        schedule = WorkScheduleFactory()
        assert schedule.user is not None
        assert schedule.name is not None
        assert schedule.start_time is not None
        assert schedule.end_time is not None
        assert len(schedule.days_of_week) > 0
        assert schedule.is_active is not None

    def test_work_schedule_str(self):
        schedule = WorkScheduleFactory()
        expected = f"{schedule.user.username} - {schedule.name}"
        assert str(schedule) == expected

    def test_work_schedule_validation(self):
        with pytest.raises(ValidationError):
            schedule = WorkScheduleFactory(
                start_time=time(17, 0),
                end_time=time(9, 0)
            )
            schedule.full_clean()

    def test_work_schedule_days_of_week(self):
        schedule = WorkScheduleFactory()
        assert all(isinstance(day, int) and 0 <= day <= 6 for day in schedule.days_of_week)
