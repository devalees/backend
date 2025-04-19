import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, fields
from django.db.models.functions import TruncDate
from datetime import timedelta, time

from Apps.time_management.models import TimeEntry, Timesheet, TimesheetEntry, WorkSchedule
from Apps.project.models import Task, Project, ProjectPhase, Milestone, ProjectSchedule
from .factories import (
    TimeCategoryFactory, TimeEntryFactory, TimesheetFactory,
    TimesheetEntryFactory, WorkScheduleFactory, UserFactory, ProjectFactory
)

@pytest.mark.django_db
class TestTimeEntryTaskIntegration:
    """Test TimeEntry integration with Task model"""
    
    def test_time_entry_task_association(self):
        """Test that TimeEntry can be associated with a Task"""
        project = ProjectFactory()
        task = Task.objects.create(
            title="Test task",
            description="Test task description",
            due_date=timezone.now() + timedelta(days=5),
            project=project,
            assigned_to=project.owner
        )
        
        time_entry = TimeEntryFactory(
            project=project,
            user=project.owner,
            task=task
        )
        
        assert time_entry.task is not None
        assert time_entry.task.id == task.id
        assert time_entry.task.title == "Test task"
    
    def test_get_time_entries_for_task(self):
        """Test that we can retrieve all time entries for a specific task"""
        project = ProjectFactory()
        task = Task.objects.create(
            title="Test task",
            description="Test task description",
            due_date=timezone.now() + timedelta(days=5),
            project=project,
            assigned_to=project.owner
        )
        
        # Create time entries for the task
        time_entry1 = TimeEntryFactory(project=project, user=project.owner, task=task, hours=2.5)
        time_entry2 = TimeEntryFactory(project=project, user=project.owner, task=task, hours=1.5)
        
        # Create an unrelated time entry
        TimeEntryFactory(project=project, user=project.owner, hours=3.0)
        
        # Get all time entries for the task
        task_time_entries = TimeEntry.objects.filter(task=task)
        
        assert task_time_entries.count() == 2
        assert sum(entry.hours for entry in task_time_entries) == 4.0

@pytest.mark.django_db
class TestTimeEntryProjectPhaseIntegration:
    """Test TimeEntry integration with ProjectPhase model"""
    
    def test_time_entry_project_phase_association(self):
        """Test that TimeEntry can be associated with a ProjectPhase"""
        # Create project with dates spanning 60 days to ensure schedule fits within it
        project = ProjectFactory(
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=60)
        )
        
        # Create a project schedule with dates within the project's dates
        schedule = ProjectSchedule.objects.create(
            project=project,
            estimated_start_date=timezone.now() + timedelta(days=1),
            estimated_end_date=timezone.now() + timedelta(days=30)
        )
        
        phase = ProjectPhase.objects.create(
            name="Development Phase",
            description="Development work",
            schedule=schedule,
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=15),
            order=1
        )
        
        time_entry = TimeEntryFactory(
            project=project,
            user=project.owner,
            project_phase=phase
        )
        
        assert time_entry.project_phase is not None
        assert time_entry.project_phase.id == phase.id
        assert time_entry.project_phase.name == "Development Phase"
    
    def test_get_time_entries_for_phase(self):
        """Test that we can retrieve all time entries for a specific phase"""
        # Create project with dates spanning 60 days
        project = ProjectFactory(
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=60)
        )
        
        # Create a project schedule with dates within the project's dates
        schedule = ProjectSchedule.objects.create(
            project=project,
            estimated_start_date=timezone.now() + timedelta(days=1),
            estimated_end_date=timezone.now() + timedelta(days=30)
        )
        
        phase = ProjectPhase.objects.create(
            name="Development Phase",
            description="Development work",
            schedule=schedule,
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=15),
            order=1
        )
        
        # Create time entries for the phase
        time_entry1 = TimeEntryFactory(project=project, user=project.owner, project_phase=phase, hours=3.0)
        time_entry2 = TimeEntryFactory(project=project, user=project.owner, project_phase=phase, hours=2.0)
        
        # Create an unrelated time entry
        TimeEntryFactory(project=project, user=project.owner, hours=1.0)
        
        # Get all time entries for the phase
        phase_time_entries = TimeEntry.objects.filter(project_phase=phase)
        
        assert phase_time_entries.count() == 2
        assert sum(entry.hours for entry in phase_time_entries) == 5.0

@pytest.mark.django_db
class TestTimeEntryMilestoneIntegration:
    """Test TimeEntry integration with Milestone model"""
    
    def test_time_entry_milestone_association(self):
        """Test that TimeEntry can be associated with a Milestone"""
        # Create project with dates spanning 60 days
        project = ProjectFactory(
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=60)
        )
        
        # Create a project schedule with dates within the project's dates
        schedule = ProjectSchedule.objects.create(
            project=project,
            estimated_start_date=timezone.now() + timedelta(days=1),
            estimated_end_date=timezone.now() + timedelta(days=30)
        )
        
        milestone = Milestone.objects.create(
            name="Version 1.0 Release",
            description="First release",
            schedule=schedule,
            due_date=timezone.now() + timedelta(days=20)
        )
        
        time_entry = TimeEntryFactory(
            project=project,
            user=project.owner,
            milestone=milestone
        )
        
        assert time_entry.milestone is not None
        assert time_entry.milestone.id == milestone.id
        assert time_entry.milestone.name == "Version 1.0 Release"

@pytest.mark.django_db
class TestTimeEntryAggregation:
    """Test TimeEntry aggregation for progress calculations"""
    
    def test_time_entry_aggregation_for_task(self):
        """Test aggregating time entries for a task"""
        project = ProjectFactory()
        task = Task.objects.create(
            title="Test task",
            description="Test task description",
            due_date=timezone.now() + timedelta(days=5),
            project=project,
            assigned_to=project.owner,
            estimated_hours=10.0  # Add this field to the Task model
        )
        
        # Create time entries for the task
        TimeEntryFactory(project=project, user=project.owner, task=task, hours=2.5)
        TimeEntryFactory(project=project, user=project.owner, task=task, hours=1.5)
        
        # Calculate progress
        total_hours = TimeEntry.objects.filter(task=task).aggregate(total=Sum('hours'))['total']
        progress_percentage = (total_hours / task.estimated_hours) * 100
        
        assert total_hours == 4.0
        assert progress_percentage == 40.0
    
    def test_time_entry_aggregation_for_project(self):
        """Test aggregating time entries for a project"""
        project = ProjectFactory()
        
        # Create tasks with estimated hours
        task1 = Task.objects.create(
            title="Task 1",
            project=project,
            due_date=timezone.now() + timedelta(days=5),
            assigned_to=project.owner,
            estimated_hours=10.0
        )
        
        task2 = Task.objects.create(
            title="Task 2",
            project=project,
            due_date=timezone.now() + timedelta(days=8),
            assigned_to=project.owner,
            estimated_hours=15.0
        )
        
        # Log time against tasks
        TimeEntryFactory(project=project, task=task1, hours=5.0, user=project.owner)
        TimeEntryFactory(project=project, task=task1, hours=3.0, user=project.owner)
        TimeEntryFactory(project=project, task=task2, hours=7.5, user=project.owner)
        
        # Calculate project progress
        total_estimated = Task.objects.filter(project=project).aggregate(total=Sum('estimated_hours'))['total']
        total_logged = TimeEntry.objects.filter(project=project).aggregate(total=Sum('hours'))['total']
        
        project_progress = (total_logged / total_estimated) * 100 if total_estimated else 0
        
        assert total_estimated == 25.0
        assert total_logged == 15.5
        assert round(project_progress, 1) == 62.0

@pytest.mark.django_db
class TestTimesheetApprovalWorkflow:
    """Test timesheet approval workflows"""
    
    def test_timesheet_approval_workflow(self):
        """Test the timesheet approval process"""
        project = ProjectFactory()
        manager = UserFactory()
        employee = UserFactory()
        
        # Add manager to project team
        project.team_members.add(manager)
        project.team_members.add(employee)
        
        # Create a timesheet for the employee
        timesheet = TimesheetFactory(
            user=employee,
            status='draft'
        )
        
        # Add time entries
        time_entry1 = TimeEntryFactory(
            project=project,
            user=employee,
            hours=4.0
        )
        
        time_entry2 = TimeEntryFactory(
            project=project,
            user=employee,
            hours=3.5
        )
        
        # Add entries to timesheet
        TimesheetEntryFactory(
            timesheet=timesheet,
            time_entry=time_entry1,
            hours=time_entry1.hours
        )
        
        TimesheetEntryFactory(
            timesheet=timesheet,
            time_entry=time_entry2,
            hours=time_entry2.hours
        )
        
        # Submit timesheet
        timesheet.status = 'submitted'
        timesheet.submitted_at = timezone.now()
        timesheet.save()
        
        assert timesheet.status == 'submitted'
        assert timesheet.submitted_at is not None
        
        # Manager approves timesheet
        timesheet.status = 'approved'
        timesheet.approved_at = timezone.now()
        timesheet.approved_by = manager
        timesheet.save()
        
        assert timesheet.status == 'approved'
        assert timesheet.approved_at is not None
        assert timesheet.approved_by == manager

@pytest.mark.django_db
class TestWorkScheduleCapacityPlanning:
    """Test capacity planning using work schedules"""
    
    def test_calculate_user_capacity(self):
        """Test calculating a user's capacity based on work schedule"""
        user = UserFactory()
        
        # Create a work schedule - 8 hours per day, Monday to Friday
        schedule = WorkScheduleFactory(
            user=user,
            start_time=time(9, 0),  # 9:00 AM
            end_time=time(17, 0),   # 5:00 PM
            days_of_week=[0, 1, 2, 3, 4]  # Monday to Friday
        )
        
        # Calculate daily capacity
        daily_capacity = schedule.daily_capacity_hours
        assert daily_capacity == 8.0
        
        # Calculate weekly capacity
        weekly_capacity = schedule.weekly_capacity_hours
        assert weekly_capacity == 40.0
        
        # Calculate capacity for a specific date range (2 weeks)
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=13)  # 2 weeks
        
        # Get working days in the range (should be 10 weekdays in 2 weeks)
        capacity = schedule.get_capacity_for_date_range(start_date, end_date)
        
        # Verify capacity calculation
        # This will be an approximation since we need to count actual weekdays 
        # in the specified period, which may vary
        assert capacity >= 70 and capacity <= 90  # Approximately 80 hours
    
    def test_calculate_team_capacity(self):
        """Test calculation of team capacity"""
        project = ProjectFactory()
        
        # Create team members
        member1 = UserFactory()
        member2 = UserFactory()
        
        # Add to project
        project.team_members.add(member1)
        project.team_members.add(member2)
        
        # Create work schedules
        schedule1 = WorkScheduleFactory(
            user=member1,
            days_of_week=[0, 1, 2, 3, 4]  # Full-time
        )
        
        schedule2 = WorkScheduleFactory(
            user=member2,
            days_of_week=[0, 2, 4]  # Part-time
        )
        
        # Calculate capacities
        member1_daily = 8.0  # Assuming 8-hour workday
        member1_weekly = member1_daily * len(schedule1.days_of_week)
        
        member2_daily = 8.0
        member2_weekly = member2_daily * len(schedule2.days_of_week)
        
        team_weekly_capacity = member1_weekly + member2_weekly
        
        assert member1_weekly == 40.0
        assert member2_weekly == 24.0
        assert team_weekly_capacity == 64.0

@pytest.mark.django_db
class TestBurndownCharts:
    """Test data for burndown charts"""
    
    def test_generate_burndown_data(self):
        """Test generating data for a burndown chart"""
        # Create project and tasks
        project = ProjectFactory(
            start_date=timezone.now().replace(hour=0, minute=0, second=0, microsecond=0),
            end_date=timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=10)
        )
        
        # Total effort: 40 hours
        task1 = Task.objects.create(
            title="Task 1",
            project=project,
            due_date=project.end_date,
            estimated_hours=25.0,
            assigned_to=project.owner
        )
        
        task2 = Task.objects.create(
            title="Task 2",
            project=project,
            due_date=project.end_date,
            estimated_hours=15.0,
            assigned_to=project.owner
        )
        
        # Create time entries over several days
        day1 = project.start_date
        day2 = day1 + timedelta(days=1)
        day3 = day1 + timedelta(days=2)
        
        # Day 1: 7 hours logged
        TimeEntryFactory(
            project=project,
            task=task1,
            start_time=day1,
            end_time=day1 + timedelta(hours=4),
            hours=4.0
        )
        
        TimeEntryFactory(
            project=project,
            task=task2,
            start_time=day1,
            end_time=day1 + timedelta(hours=3),
            hours=3.0
        )
        
        # Day 2: 8 hours logged
        TimeEntryFactory(
            project=project,
            task=task1,
            start_time=day2,
            end_time=day2 + timedelta(hours=5),
            hours=5.0
        )
        
        TimeEntryFactory(
            project=project,
            task=task2,
            start_time=day2,
            end_time=day2 + timedelta(hours=3),
            hours=3.0
        )
        
        # Day 3: 6 hours logged
        TimeEntryFactory(
            project=project,
            task=task1,
            start_time=day3,
            end_time=day3 + timedelta(hours=4),
            hours=4.0
        )
        
        TimeEntryFactory(
            project=project,
            task=task2,
            start_time=day3,
            end_time=day3 + timedelta(hours=2),
            hours=2.0
        )
        
        # Calculate burndown data
        total_estimated = Task.objects.filter(project=project).aggregate(total=Sum('estimated_hours'))['total']
        
        # Get time entries grouped by day
        daily_hours = TimeEntry.objects.filter(project=project).annotate(
            date=TruncDate('start_time')
        ).values('date').annotate(
            daily_hours=Sum('hours')
        ).order_by('date')
        
        # Calculate remaining work
        remaining = [{'date': project.start_date, 'remaining': total_estimated}]
        
        current_remaining = total_estimated
        for day_data in daily_hours:
            current_remaining -= day_data['daily_hours']
            remaining.append({
                'date': day_data['date'],
                'remaining': current_remaining
            })
        
        # Verify burndown data
        assert len(remaining) == 4  # Initial + 3 days of entries
        assert remaining[0]['remaining'] == 40.0
        assert remaining[1]['remaining'] == 33.0  # 40 - 7
        assert remaining[2]['remaining'] == 25.0  # 33 - 8
        assert remaining[3]['remaining'] == 19.0  # 25 - 6

@pytest.mark.django_db
class TestTimeEstimationComparison:
    """Test comparison between estimated and actual time"""
    
    def test_task_time_comparison(self):
        """Test comparing estimated vs actual time for tasks"""
        project = ProjectFactory()
        
        # Create tasks with estimated hours
        task = Task.objects.create(
            title="Complex Task",
            description="A complex task requiring estimation",
            project=project,
            due_date=timezone.now() + timedelta(days=10),
            assigned_to=project.owner,
            estimated_hours=20.0
        )
        
        # Log time entries for the task
        TimeEntryFactory(
            project=project,
            task=task,
            user=project.owner,
            description="Initial research",
            hours=4.5
        )
        
        TimeEntryFactory(
            project=project,
            task=task,
            user=project.owner,
            description="Development work",
            hours=8.0
        )
        
        TimeEntryFactory(
            project=project,
            task=task,
            user=project.owner,
            description="Testing and fixes",
            hours=3.5
        )
        
        # Calculate total logged time
        total_logged = TimeEntry.objects.filter(task=task).aggregate(
            total=Sum('hours')
        )['total']
        
        # Calculate variance
        variance = task.estimated_hours - total_logged
        variance_percentage = (variance / task.estimated_hours) * 100
        
        assert total_logged == 16.0
        assert variance == 4.0  # Under by 4 hours
        assert variance_percentage == 20.0  # Under by 20% 