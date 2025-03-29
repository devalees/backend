import pytest
from django.utils import timezone
from ..serializers import ProjectSerializer, TaskSerializer
from .factories import ProjectFactory, TaskFactory

pytestmark = pytest.mark.django_db

class TestProjectSerializer:
    def test_serialize_project(self):
        project = ProjectFactory()
        serializer = ProjectSerializer(project)
        data = serializer.data
        
        assert data['id'] == project.id
        assert data['title'] == project.title
        assert data['description'] == project.description
        assert data['status'] == project.status
        assert data['priority'] == project.priority
        assert data['owner']['id'] == project.owner.id
        assert data['organization']['id'] == project.organization.id
        assert data['task_count'] == project.tasks.count()

    def test_deserialize_project(self):
        project_data = {
            'title': 'Test Project',
            'description': 'Test Description',
            'start_date': timezone.now().isoformat(),
            'end_date': (timezone.now() + timezone.timedelta(days=30)).isoformat(),
            'status': 'new',
            'priority': 'medium',
            'owner_id': ProjectFactory().owner.id,
            'organization_id': ProjectFactory().organization.id,
        }
        
        serializer = ProjectSerializer(data=project_data)
        assert serializer.is_valid()
        
        project = serializer.save()
        assert project.title == project_data['title']
        assert project.description == project_data['description']
        assert project.status == project_data['status']
        assert project.priority == project_data['priority']

    def test_invalid_dates(self):
        project_data = {
            'title': 'Test Project',
            'start_date': timezone.now().isoformat(),
            'end_date': (timezone.now() - timezone.timedelta(days=1)).isoformat(),
            'owner_id': ProjectFactory().owner.id,
            'organization_id': ProjectFactory().organization.id,
        }
        
        serializer = ProjectSerializer(data=project_data)
        assert not serializer.is_valid()
        assert 'Start date must be before end date' in str(serializer.errors)

class TestTaskSerializer:
    def test_serialize_task(self):
        task = TaskFactory()
        serializer = TaskSerializer(task)
        data = serializer.data
        
        assert data['id'] == task.id
        assert data['title'] == task.title
        assert data['description'] == task.description
        assert data['status'] == task.status
        assert data['priority'] == task.priority
        assert data['project'] == task.project.id
        assert data['assigned_to']['id'] == task.assigned_to.id

    def test_deserialize_task(self):
        project = ProjectFactory()
        task_data = {
            'title': 'Test Task',
            'description': 'Test Description',
            'due_date': timezone.now().isoformat(),
            'status': 'todo',
            'priority': 'medium',
            'project': project.id,
            'assigned_to_id': project.owner.id,
        }
        
        serializer = TaskSerializer(data=task_data)
        assert serializer.is_valid()
        
        task = serializer.save()
        assert task.title == task_data['title']
        assert task.description == task_data['description']
        assert task.status == task_data['status']
        assert task.priority == task_data['priority']
        assert task.project == project
        assert task.assigned_to == project.owner

    def test_invalid_parent_task(self):
        task = TaskFactory()
        other_project_task = TaskFactory()
        
        task_data = {
            'title': 'Test Task',
            'description': 'Test Description',
            'due_date': timezone.now().isoformat(),
            'status': 'todo',
            'priority': 'medium',
            'project': task.project.id,
            'parent_task': other_project_task.id,
        }
        
        serializer = TaskSerializer(data=task_data)
        assert not serializer.is_valid()
        assert 'Parent task must belong to the same project' in str(serializer.errors)
