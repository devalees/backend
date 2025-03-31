import factory
from datetime import time
from django.utils import timezone
from django.contrib.auth import get_user_model
from Apps.project.models import Project
from Apps.entity.models import Organization
from Apps.time_management.models import (
    TimeCategory, TimeEntry, Timesheet, TimesheetEntry, WorkSchedule
)

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')

class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: f'Organization {n}')
    created_by = factory.SubFactory(UserFactory)

class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    title = factory.Sequence(lambda n: f'Project {n}')
    description = factory.Faker('sentence')
    start_date = factory.LazyFunction(timezone.now)
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + timezone.timedelta(days=30))
    status = factory.Iterator(['new', 'in_progress', 'on_hold', 'completed'])
    priority = factory.Iterator(['low', 'medium', 'high'])
    owner = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)

class TimeCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimeCategory

    name = factory.Sequence(lambda n: f'Category {n}')
    description = factory.Faker('sentence')
    is_billable = factory.Faker('boolean')
    created_by = factory.SubFactory(UserFactory)

class TimeEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimeEntry

    user = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
    category = factory.SubFactory(TimeCategoryFactory)
    description = factory.Faker('sentence')
    start_time = factory.LazyFunction(timezone.now)
    end_time = factory.LazyAttribute(lambda obj: obj.start_time + timezone.timedelta(hours=2))
    hours = factory.LazyAttribute(lambda obj: (obj.end_time - obj.start_time).total_seconds() / 3600)
    is_billable = factory.Faker('boolean')
    created_by = factory.SubFactory(UserFactory)

class TimesheetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Timesheet

    user = factory.SubFactory(UserFactory)
    start_date = factory.Sequence(lambda n: (timezone.now() + timezone.timedelta(days=n*7)).date())
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + timezone.timedelta(days=7))
    status = factory.Iterator(['draft', 'submitted', 'approved', 'rejected'])
    notes = factory.Faker('paragraph')
    submitted_at = factory.LazyAttribute(
        lambda obj: timezone.now() if obj.status in ['submitted', 'approved', 'rejected'] else None
    )
    approved_at = factory.LazyAttribute(
        lambda obj: timezone.now() if obj.status == 'approved' else None
    )
    approved_by = factory.LazyAttribute(
        lambda obj: UserFactory() if obj.status == 'approved' else None
    )

class TimesheetEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimesheetEntry

    timesheet = factory.SubFactory(TimesheetFactory)
    time_entry = factory.SubFactory(TimeEntryFactory)
    date = factory.LazyAttribute(lambda obj: obj.timesheet.start_date)
    hours = factory.Faker('pyfloat', min_value=0, max_value=24)
    category = factory.SubFactory(TimeCategoryFactory)
    description = factory.Faker('sentence')

class WorkScheduleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkSchedule

    user = factory.SubFactory(UserFactory)
    start_time = factory.LazyFunction(lambda: time(9, 0))  # 9:00 AM
    end_time = factory.LazyFunction(lambda: time(17, 0))   # 5:00 PM
    days_of_week = factory.List([0, 1, 2, 3, 4])  # Monday to Friday
    is_active = factory.Faker('boolean')
