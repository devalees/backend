import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError
from Apps.project.models import Project, ProjectDiscussion
from Apps.users.models import User
from .factories import ProjectFactory

pytestmark = pytest.mark.django_db

class TestProjectDiscussion:
    def test_create_discussion(self, monkeypatch):
        # Create a project
        project = ProjectFactory()
        
        # Create a discussion for the project
        discussion = ProjectDiscussion.objects.create(
            project=project,
            title="Test Discussion",
            content="This is a test discussion content",
            created_by=project.owner,
            updated_by=project.owner
        )
        
        assert discussion.pk is not None
        assert discussion.title == "Test Discussion"
        assert discussion.content == "This is a test discussion content"
        assert discussion.project == project
        assert discussion.created_by == project.owner
        assert discussion.is_active is True
        assert discussion.created_at is not None
        assert discussion.updated_at is not None
    
    def test_discussion_str(self):
        project = ProjectFactory(title="Project Alpha")
        discussion = ProjectDiscussion.objects.create(
            project=project,
            title="Test Discussion",
            content="This is a test discussion content",
            created_by=project.owner,
            updated_by=project.owner
        )
        assert str(discussion) == "Test Discussion - Project Alpha"
    
    def test_discussion_without_title(self):
        project = ProjectFactory()
        with pytest.raises(ValidationError):
            discussion = ProjectDiscussion(
                project=project,
                title="",
                content="This is a test discussion content",
                created_by=project.owner,
                updated_by=project.owner
            )
            discussion.full_clean()
    
    def test_discussion_without_project(self):
        project = ProjectFactory()
        # Using ValidationError instead of IntegrityError since Django's validation
        # catches this before it gets to database IntegrityError
        with pytest.raises(ValidationError):
            discussion = ProjectDiscussion(
                title="Test Discussion",
                content="This is a test discussion content",
                created_by=project.owner,
                updated_by=project.owner
            )
            discussion.full_clean()
    
    def test_mark_discussion_inactive(self):
        project = ProjectFactory()
        discussion = ProjectDiscussion.objects.create(
            project=project,
            title="Test Discussion",
            content="This is a test discussion content",
            created_by=project.owner,
            updated_by=project.owner
        )
        
        # Ensure the discussion was created as active
        assert discussion.is_active is True
        
        # Mark discussion as inactive
        discussion.is_active = False
        discussion.save()
        
        # Verify the instance in memory was updated
        assert discussion.is_active is False
    
    def test_discussion_ordering(self):
        project = ProjectFactory()
        
        # Create discussions in reverse order
        discussion3 = ProjectDiscussion.objects.create(
            project=project,
            title="Discussion 3",
            content="Content 3",
            created_by=project.owner,
            updated_by=project.owner
        )
        
        discussion2 = ProjectDiscussion.objects.create(
            project=project,
            title="Discussion 2",
            content="Content 2",
            created_by=project.owner,
            updated_by=project.owner
        )
        
        discussion1 = ProjectDiscussion.objects.create(
            project=project,
            title="Discussion 1",
            content="Content 1",
            created_by=project.owner,
            updated_by=project.owner
        )
        
        # Get ordered discussions
        discussions = ProjectDiscussion.objects.filter(project=project)
        
        # Should be ordered by created_at in descending order (newest first)
        assert discussions[0] == discussion1
        assert discussions[1] == discussion2
        assert discussions[2] == discussion3 