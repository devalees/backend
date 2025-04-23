import factory
from datetime import time, datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from Apps.project.models import Project
from Apps.entity.models import Organization
from Apps.time_management.models import (
    TimeCategory, TimeEntry, Timesheet, TimesheetEntry, WorkSchedule
)
from Apps.core.models import get_current_user, set_current_user

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'password')
    
    class Meta:
        model = User
        django_get_or_create = ('username',)
        skip_postgeneration_save = True

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
    created_by = factory.SelfAttribute('owner')

class TimeCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimeCategory
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f'Category {n}')
    description = factory.Faker('sentence')
    is_billable = factory.Faker('boolean')
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SelfAttribute('created_by')

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
    created_by = factory.SelfAttribute('user')
    updated_by = factory.SelfAttribute('user')

class TimesheetFactory(factory.django.DjangoModelFactory):
    """Factory for creating test Timesheet instances."""

    class Meta:
        model = Timesheet

    user = factory.SubFactory(UserFactory)
    start_date = factory.LazyFunction(lambda: timezone.now().date().replace(day=1))
    end_date = factory.LazyFunction(lambda: (timezone.now().date().replace(day=1) + timedelta(days=30)).replace(day=1) - timedelta(days=1))
    status = 'draft'
    total_hours = 0
    notes = factory.Faker('sentence')
    submitted_at = None
    approved_at = None
    approved_by = None
    rejected_at = None
    rejected_by = None
    rejection_reason = ''
    
    @factory.post_generation
    def make_submitted(self, create, extracted, **kwargs):
        """Post-generation hook to make the timesheet submitted if needed."""
        if extracted:
            self.status = 'submitted'
            self.submitted_at = timezone.now()
            self.save()
            
    @factory.post_generation
    def make_approved(self, create, extracted, **kwargs):
        """Post-generation hook to make the timesheet approved if needed."""
        if extracted:
            if self.status != 'submitted':
                self.status = 'submitted'
                self.submitted_at = timezone.now()
            approver = kwargs.get('approver', UserFactory())
            self.approve(approver)
            
    @factory.post_generation
    def make_rejected(self, create, extracted, **kwargs):
        """Post-generation hook to make the timesheet rejected if needed."""
        if extracted:
            if self.status != 'submitted':
                self.status = 'submitted'
                self.submitted_at = timezone.now()
            rejector = kwargs.get('rejector', UserFactory())
            reason = kwargs.get('reason', 'Test rejection reason')
            self.reject(rejector, reason)

class TimesheetEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimesheetEntry

    timesheet = factory.SubFactory(TimesheetFactory)
    time_entry = factory.SubFactory(TimeEntryFactory)
    date = factory.LazyAttribute(lambda obj: obj.timesheet.start_date)
    hours = factory.LazyFunction(lambda: round(float(2.0), 2))  # Simple fixed value to start with
    category = factory.SubFactory(TimeCategoryFactory)
    description = factory.Faker('sentence')
    notes = factory.Faker('paragraph')
    created_by = factory.LazyAttribute(lambda obj: obj.timesheet.user)
    updated_by = factory.LazyAttribute(lambda obj: obj.timesheet.user)

class WorkScheduleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkSchedule

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'Schedule {n}')
    start_time = factory.LazyFunction(lambda: time(9, 0))  # 9:00 AM
    end_time = factory.LazyFunction(lambda: time(17, 0))   # 5:00 PM
    days_of_week = factory.List([0, 1, 2, 3, 4])  # Monday to Friday
    is_active = factory.Faker('boolean')
    created_by = factory.SelfAttribute('user')
    updated_by = factory.SelfAttribute('user')

# Helper function to set current user in tests
@factory.post_generation
def with_current_user(obj, create, extracted, **kwargs):
    """
    Post-generation hook to set the current user for model instances.
    This helps with automatic user tracking when creating instances.
    Usage: instance = ModelFactory.create(with_current_user=user)
    """
    if not create:
        return
        
    if extracted:
        previous_user = get_current_user()
        set_current_user(extracted)
        try:
            obj.save()  # Save again with the current user set
        finally:
            set_current_user(previous_user)
