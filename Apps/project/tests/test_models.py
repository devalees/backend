import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from Apps.project.models import Project, Task
from .factories import ProjectFactory, TaskFactory

pytestmark = pytest.mark.django_db

class TestProject:
    def test_create_project(self):
        project = ProjectFactory()
        assert project.pk is not None
        assert project.title
        assert project.status == Project.Status.NEW
        assert project.priority == Project.Priority.MEDIUM
        assert project.owner
        assert project.organization
        assert project.created_by == project.owner
        assert project.updated_by == project.owner

    def test_project_str(self):
        project = ProjectFactory(title="Test Project")
        assert str(project) == "Test Project"

    def test_invalid_dates(self):
        with pytest.raises(ValidationError):
            ProjectFactory(
                start_date=timezone.now() + timezone.timedelta(days=1),
                end_date=timezone.now()
            )

    def test_add_team_members(self):
        project = ProjectFactory()
        user1 = project.owner
        user2 = ProjectFactory().owner
        
        project.team_members.add(user1, user2)
        assert project.team_members.count() == 2
        assert user1 in project.team_members.all()
        assert user2 in project.team_members.all()

class TestTask:
    def test_create_task(self):
        task = TaskFactory()
        assert task.pk is not None
        assert task.title
        assert task.status == Task.Status.TODO
        assert task.priority == Task.Priority.MEDIUM
        assert task.project
        assert task.assigned_to
        assert task.created_by == task.assigned_to
        assert task.updated_by == task.assigned_to

    def test_task_str(self):
        task = TaskFactory(title="Test Task")
        assert str(task) == "Test Task"

    def test_task_with_parent(self):
        parent_task = TaskFactory()
        child_task = TaskFactory(project=parent_task.project, parent_task=parent_task)
        assert child_task.parent_task == parent_task
        assert child_task in parent_task.subtasks.all()

    def test_invalid_parent_task(self):
        task1 = TaskFactory()
        task2 = TaskFactory()  # Different project
        
        with pytest.raises(ValidationError):
            task2.parent_task = task1
            task2.clean()

    def test_invalid_due_date(self):
        project = ProjectFactory(
            end_date=timezone.now() + timezone.timedelta(days=10)
        )
        with pytest.raises(ValidationError):
            TaskFactory(
                project=project,
                due_date=timezone.now() + timezone.timedelta(days=20)
            )
