from rest_framework import serializers
from .models import Project, Task, ProjectTemplate, TaskTemplate
from Apps.users.serializers import UserSerializer
from Apps.entity.serializers import OrganizationSerializer
from Apps.users.models import User
from Apps.entity.models import Organization
from django.utils import timezone

class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        source='assigned_to',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'due_date', 'status', 'priority',
            'project', 'assigned_to', 'assigned_to_id', 'parent_task',
            'created_by', 'updated_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']

    def validate(self, data):
        if 'parent_task' in data and data['parent_task']:
            if data['parent_task'].project != data.get('project', self.instance.project if self.instance else None):
                raise serializers.ValidationError("Parent task must belong to the same project")
        return data

class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        source='owner',
        queryset=User.objects.all(),
        write_only=True
    )
    team_members = UserSerializer(many=True, read_only=True)
    team_member_ids = serializers.PrimaryKeyRelatedField(
        source='team_members',
        queryset=User.objects.all(),
        write_only=True,
        many=True,
        required=False
    )
    organization = OrganizationSerializer(read_only=True)
    organization_id = serializers.PrimaryKeyRelatedField(
        source='organization',
        queryset=Organization.objects.all(),
        write_only=True
    )
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'status', 'priority', 'owner', 'owner_id', 'team_members',
            'team_member_ids', 'organization', 'organization_id',
            'created_by', 'updated_by', 'created_at', 'updated_at',
            'tasks', 'task_count'
        ]
        read_only_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']

    def get_task_count(self, obj):
        return obj.tasks.count()

    def validate(self, data):
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("Start date must be before end date")
        return data 

class TaskTemplateSerializer(serializers.ModelSerializer):
    subtask_templates = serializers.SerializerMethodField()

    class Meta:
        model = TaskTemplate
        fields = [
            'id', 'title', 'description', 'estimated_duration',
            'default_status', 'default_priority', 'project_template',
            'parent_task_template', 'order', 'subtask_templates',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_subtask_templates(self, obj):
        subtasks = obj.subtask_templates.all()
        return TaskTemplateSerializer(subtasks, many=True).data

class ProjectTemplateSerializer(serializers.ModelSerializer):
    task_templates = TaskTemplateSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectTemplate
        fields = [
            'id', 'title', 'description', 'estimated_duration',
            'default_status', 'default_priority', 'organization',
            'task_templates', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def create_project(self, start_date, end_date, owner=None):
        """
        Create a new project from this template
        """
        owner = owner or self.context['request'].user
        project = Project.objects.create(
            title=self.instance.title,
            description=self.instance.description,
            start_date=start_date,
            end_date=end_date,
            status=self.instance.default_status,
            priority=self.instance.default_priority,
            organization=self.instance.organization,
            owner=owner,
            created_by=self.context['request'].user,
            updated_by=self.context['request'].user
        )

        # Create tasks from task templates
        task_map = {}  # Map template ID to actual task
        for task_template in self.instance.task_templates.filter(parent_task_template=None):
            self._create_task_from_template(task_template, project, task_map)

        return project

    def _create_task_from_template(self, task_template, project, task_map):
        """
        Recursively create tasks from templates
        """
        due_date = project.start_date + timezone.timedelta(days=task_template.estimated_duration)
        task = Task.objects.create(
            title=task_template.title,
            description=task_template.description,
            due_date=due_date,
            status=task_template.default_status,
            priority=task_template.default_priority,
            project=project,
            parent_task=task_map.get(task_template.parent_task_template_id) if task_template.parent_task_template else None,
            created_by=self.context['request'].user,
            updated_by=self.context['request'].user
        )
        task_map[task_template.id] = task

        # Create subtasks
        for subtask_template in task_template.subtask_templates.all():
            self._create_task_from_template(subtask_template, project, task_map)

        return task 