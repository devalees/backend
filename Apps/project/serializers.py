from rest_framework import serializers
from .models import Project, Task, ProjectTemplate, TaskTemplate, Milestone, ProjectPhase, ProjectSchedule, ProjectDiscussion, DiscussionAttachment, DiscussionNotification
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
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'due_date', 'status', 'priority',
            'project', 'assigned_to', 'assigned_to_id', 'parent_task',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name', 
            'created_at', 'updated_at'
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
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    tasks = TaskSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'start_date', 'end_date',
            'status', 'priority', 'owner', 'owner_id', 'team_members',
            'team_member_ids', 'organization', 'organization_id',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at', 'tasks', 'task_count'
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
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)

    class Meta:
        model = TaskTemplate
        fields = [
            'id', 'title', 'description', 'estimated_duration',
            'default_status', 'default_priority', 'project_template',
            'parent_task_template', 'order', 'subtask_templates',
            'created_at', 'updated_at', 'created_by', 'created_by_name',
            'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

    def get_subtask_templates(self, obj):
        subtasks = obj.subtask_templates.all()
        return TaskTemplateSerializer(subtasks, many=True).data

class ProjectTemplateSerializer(serializers.ModelSerializer):
    task_templates = TaskTemplateSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)

    class Meta:
        model = ProjectTemplate
        fields = [
            'id', 'title', 'description', 'estimated_duration',
            'default_status', 'default_priority', 'organization',
            'task_templates', 'created_at', 'updated_at',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name'
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

class MilestoneSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = Milestone
        fields = [
            'id', 'name', 'description', 'schedule', 'phase',
            'due_date', 'status', 'completion_date', 'created_at',
            'updated_at', 'created_by', 'created_by_name', 
            'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'completion_date']

    def validate(self, data):
        # Validate due date is within schedule dates
        if 'due_date' in data and 'schedule' in data:
            schedule = data['schedule']
            if data['due_date'] < schedule.estimated_start_date:
                raise serializers.ValidationError(
                    {'due_date': 'Milestone due date cannot be before schedule start date'}
                )
            if data['due_date'] > schedule.estimated_end_date:
                raise serializers.ValidationError(
                    {'due_date': 'Milestone due date cannot be after schedule end date'}
                )

        # Validate due date is within phase dates if phase provided
        if 'due_date' in data and 'phase' in data and data['phase']:
            phase = data['phase']
            if data['due_date'] < phase.start_date:
                raise serializers.ValidationError(
                    {'due_date': 'Milestone due date cannot be before phase start date'}
                )
            if data['due_date'] > phase.end_date:
                raise serializers.ValidationError(
                    {'due_date': 'Milestone due date cannot be after phase end date'}
                )
            
            # Validate phase belongs to the same schedule
            if 'schedule' in data and phase.schedule != data['schedule']:
                raise serializers.ValidationError(
                    {'phase': 'Phase must belong to the same schedule as the milestone'}
                )
        
        return data

class ProjectPhaseSerializer(serializers.ModelSerializer):
    milestones = MilestoneSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = ProjectPhase
        fields = [
            'id', 'name', 'description', 'schedule', 'start_date',
            'end_date', 'order', 'is_active', 'progress', 'milestones',
            'created_at', 'updated_at', 'created_by', 'created_by_name', 
            'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'progress']

    def validate(self, data):
        # Validate date range
        if 'start_date' in data and 'end_date' in data:
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError(
                    {'start_date': 'Start date must be before end date'}
                )
        
        # Validate phase dates are within schedule dates
        if 'schedule' in data and ('start_date' in data or 'end_date' in data):
            schedule = data['schedule']
            start_date = data.get('start_date', getattr(self.instance, 'start_date', None))
            end_date = data.get('end_date', getattr(self.instance, 'end_date', None))
            
            if start_date and start_date < schedule.estimated_start_date:
                raise serializers.ValidationError(
                    {'start_date': 'Phase start date cannot be before schedule start date'}
                )
            if end_date and end_date > schedule.estimated_end_date:
                raise serializers.ValidationError(
                    {'end_date': 'Phase end date cannot be after schedule end date'}
                )
                
        return data

class ProjectScheduleSerializer(serializers.ModelSerializer):
    phases = ProjectPhaseSerializer(many=True, read_only=True)
    milestones = MilestoneSerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = ProjectSchedule
        fields = [
            'id', 'project', 'estimated_start_date', 'estimated_end_date',
            'description', 'is_baseline', 'progress', 'phases', 'milestones',
            'duration', 'created_at', 'updated_at', 'created_by', 
            'created_by_name', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by', 'progress']

    def get_duration(self, obj):
        return obj.get_duration()

    def validate(self, data):
        # Validate date range
        if 'estimated_start_date' in data and 'estimated_end_date' in data:
            if data['estimated_start_date'] > data['estimated_end_date']:
                raise serializers.ValidationError(
                    {'estimated_start_date': 'Start date must be before end date'}
                )
        
        # Validate project
        if 'project' in data and 'estimated_start_date' in data:
            if data['estimated_start_date'] < data['project'].start_date:
                raise serializers.ValidationError(
                    {'estimated_start_date': 'Schedule start date cannot be before project start date'}
                )
        
        if 'project' in data and 'estimated_end_date' in data:
            if data['estimated_end_date'] > data['project'].end_date:
                raise serializers.ValidationError(
                    {'estimated_end_date': 'Schedule end date cannot be after project end date'}
                )
        
        return data

class ProjectDiscussionSerializer(serializers.ModelSerializer):
    """
    Serializer for the ProjectDiscussion model.
    """
    created_by_name = serializers.SerializerMethodField()
    attachment_count = serializers.SerializerMethodField()
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = ProjectDiscussion
        fields = [
            'id', 'project', 'title', 'content', 'is_active',
            'created_at', 'created_by', 'created_by_name',
            'updated_at', 'updated_by', 'updated_by_name', 'attachment_count'
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 'updated_at', 'updated_by', 'attachment_count']
        extra_kwargs = {
            'project': {'required': False}
        }
    
    def get_created_by_name(self, obj):
        """Get the name of the user who created the discussion"""
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return ""
    
    def get_attachment_count(self, obj):
        """Get the number of attachments for the discussion"""
        return obj.attachments.count()
    
    def validate(self, data):
        """
        Custom validation for ProjectDiscussion.
        """
        # Ensure title is not empty when provided
        if 'title' in data and not data['title'].strip():
            raise serializers.ValidationError({'title': 'Title cannot be empty'})
        
        # Ensure content is not empty when provided
        if 'content' in data and not data['content'].strip():
            raise serializers.ValidationError({'content': 'Content cannot be empty'})
        
        return data
    
    def create(self, validated_data):
        """
        Create and return a new ProjectDiscussion instance, given the validated data.
        """
        # Set created_by and updated_by from the context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
            validated_data['updated_by'] = request.user
        
        # Get project from context if not in validated_data
        project_pk = self.context.get('project_pk')
        if project_pk and 'project' not in validated_data:
            project = Project.objects.get(pk=project_pk)
            validated_data['project'] = project
        
        # Create the discussion using model's create method
        instance = ProjectDiscussion.objects.create(**validated_data)
        return instance
    
    def update(self, instance, validated_data):
        """
        Update and return an existing ProjectDiscussion instance, given the validated data.
        """
        # Set updated_by from the context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user
        
        # Remove project from validated_data if present to prevent change
        if 'project' in validated_data:
            # Only raise error if trying to change to a different project
            if validated_data['project'].pk != instance.project.pk:
                raise serializers.ValidationError({'project': 'Cannot change the project for an existing discussion'})
            # Remove it to avoid unnecessary update
            validated_data.pop('project')
        
        # Update fields manually to avoid validation issues
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Save the instance
        instance.save()
        
        # Create notifications for team members about the update
        instance._create_notifications_for_team('updated')
        
        return instance

class DiscussionAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the DiscussionAttachment model.
    """
    file_url = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = DiscussionAttachment
        fields = [
            'id', 'discussion', 'file', 'filename', 'description', 
            'file_size', 'content_type', 'created_at', 'created_by',
            'created_by_name', 'updated_at', 'updated_by', 'updated_by_name', 
            'file_url'
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 'updated_at', 'updated_by', 
                           'file_size', 'content_type', 'filename', 'file_url']
        extra_kwargs = {
            'discussion': {'required': False}
        }
    
    def get_file_url(self, obj):
        """Get the URL for the attachment file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None
    
    def create(self, validated_data):
        """
        Create and return a new DiscussionAttachment instance, given the validated data.
        """
        # Set created_by and updated_by from the context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
            validated_data['updated_by'] = request.user
        
        # Create attachment using model's create method to bypass validation issues
        attachment = DiscussionAttachment.objects.create(**validated_data)
        
        # Create notification for team members about the new attachment
        discussion = attachment.discussion
        discussion._create_notifications_for_team('attachment')
        
        return attachment

class DiscussionNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for the DiscussionNotification model.
    """
    discussion_title = serializers.SerializerMethodField()
    project_id = serializers.SerializerMethodField()
    notification_text = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True, allow_null=True)

    class Meta:
        model = DiscussionNotification
        fields = [
            'id', 'discussion', 'discussion_title', 'project_id',
            'user', 'notification_type', 'notification_text',
            'is_read', 'read_at', 'created_at', 'created_by', 'created_by_name',
            'updated_at', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['created_at', 'created_by', 'updated_at', 'updated_by', 
                           'discussion_title', 'project_id', 'notification_text']
    
    def get_discussion_title(self, obj):
        """Get the title of the discussion"""
        return obj.discussion.title if obj.discussion else ""
    
    def get_project_id(self, obj):
        """Get the ID of the project"""
        return obj.discussion.project.id if obj.discussion and obj.discussion.project else None
    
    def get_notification_text(self, obj):
        """Get a descriptive text for the notification"""
        if not obj.discussion:
            return ""
        
        notification_type = obj.notification_type
        actor_name = f"{obj.created_by.first_name} {obj.created_by.last_name}" if obj.created_by else "Someone"
        
        if notification_type == 'created':
            return f"{actor_name} created a new discussion: {obj.discussion.title}"
        elif notification_type == 'updated':
            return f"{actor_name} updated discussion: {obj.discussion.title}"
        elif notification_type == 'comment':
            return f"{actor_name} commented on discussion: {obj.discussion.title}"
        elif notification_type == 'mention':
            return f"{actor_name} mentioned you in discussion: {obj.discussion.title}"
        elif notification_type == 'attachment':
            return f"{actor_name} added an attachment to discussion: {obj.discussion.title}"
        else:
            return f"New activity in discussion: {obj.discussion.title}" 