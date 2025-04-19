import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from Apps.project.models import Project, ProjectDiscussion, DiscussionNotification
from Apps.users.models import User
from Apps.communication.models import Notification
from .factories import ProjectFactory

pytestmark = pytest.mark.django_db

class TestDiscussionNotifications:
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def project(self):
        project = ProjectFactory()
        # Add a team member
        team_member = ProjectFactory().owner
        project.team_members.add(team_member)
        return project
    
    @pytest.fixture
    def discussion(self, project):
        return ProjectDiscussion.objects.create(
            project=project,
            title="Test Discussion",
            content="This is a test discussion content",
            created_by=project.owner,
            updated_by=project.owner
        )
    
    def test_create_discussion_notification(self, project, discussion):
        """Test that notifications are created when a discussion is created"""
        # Get team members
        team_members = list(project.team_members.all())
        
        # Check if notifications were created for team members (excluding owner who created the discussion)
        for member in team_members:
            # Skip the owner of the discussion
            if member == discussion.created_by:
                continue
                
            notification = DiscussionNotification.objects.filter(
                discussion=discussion,
                user=member,
                notification_type='created'
            ).first()
            
            assert notification is not None
            assert notification.is_read is False
    
    def test_mark_notification_as_read(self, api_client, project, discussion):
        """Test marking a notification as read"""
        # Force authentication with a team member
        team_member = project.team_members.first()
        api_client.force_authenticate(user=team_member)
        
        # Create notification for the team member
        notification = DiscussionNotification.objects.create(
            discussion=discussion,
            user=team_member,
            notification_type='created',
            created_by=discussion.created_by,
            updated_by=discussion.created_by
        )
        
        assert notification is not None
        assert notification.is_read is False
        
        # Mark as read
        url = reverse('project:discussion-notifications-mark-read', kwargs={
            'project_pk': project.pk,
            'discussion_pk': discussion.pk,
            'pk': notification.pk
        })
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Refresh notification
        notification.refresh_from_db()
        assert notification.is_read is True
    
    def test_list_user_notifications(self, api_client, project, discussion):
        """Test listing notifications for a user"""
        # Force authentication with a team member
        team_member = project.team_members.first()
        api_client.force_authenticate(user=team_member)
        
        # Create notification for the team member
        notification = DiscussionNotification.objects.create(
            discussion=discussion,
            user=team_member,
            notification_type='created',
            created_by=discussion.created_by,
            updated_by=discussion.created_by
        )
        
        url = reverse('project:user-discussion-notifications-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Handle both paginated and non-paginated responses
        if 'results' in response.data:
            notification_list = response.data['results']
        else:
            notification_list = response.data
        
        # Check that we have at least one notification
        assert len(notification_list) >= 1
        
        # Find the notification for the discussion
        found = False
        for notification_data in notification_list:
            # Check if the notification belongs to our discussion
            if 'discussion' in notification_data and notification_data['discussion'] == discussion.pk:
                found = True
                assert notification_data['is_read'] is False
                assert notification_data['notification_type'] == 'created'
                break
        
        assert found, "Notification for the discussion not found in the response"
    
    def test_notification_for_discussion_update(self, api_client, project, discussion):
        """Test that notifications are created when a discussion is updated"""
        # Reset notifications
        DiscussionNotification.objects.all().delete()
        
        # Force authentication with project owner
        api_client.force_authenticate(user=project.owner)
        
        # Update the discussion
        url = reverse('project:project-discussions-detail', kwargs={
            'project_pk': project.pk,
            'pk': discussion.pk
        })
        
        data = {
            'title': 'Updated Discussion Title',
            'content': 'Updated content',
            'is_active': True,
            'project': project.pk
        }
        
        response = api_client.put(url, data=data, format='json')
        assert response.status_code == status.HTTP_200_OK
        
        # Get team members
        team_members = list(project.team_members.all())
        
        # Check if notifications were created for team members (excluding owner who made the update)
        for member in team_members:
            # Skip the owner
            if member == project.owner:
                continue
                
            notification = DiscussionNotification.objects.filter(
                discussion=discussion,
                user=member,
                notification_type='updated'
            ).first()
            
            assert notification is not None
            assert notification.is_read is False
    
    def test_bulk_mark_notifications_as_read(self, api_client, project, discussion):
        """Test marking all notifications as read for a user"""
        # Force authentication with a team member
        team_member = project.team_members.first()
        api_client.force_authenticate(user=team_member)
        
        # Create notifications for the team member
        DiscussionNotification.objects.create(
            discussion=discussion,
            user=team_member,
            notification_type='created',
            created_by=discussion.created_by,
            updated_by=discussion.created_by
        )
        
        # Create another discussion and notification
        discussion2 = ProjectDiscussion.objects.create(
            project=project,
            title="Test Discussion 2",
            content="This is another test discussion",
            created_by=project.owner,
            updated_by=project.owner
        )
        
        DiscussionNotification.objects.create(
            discussion=discussion2,
            user=team_member,
            notification_type='created',
            created_by=discussion2.created_by,
            updated_by=discussion2.created_by
        )
        
        # Verify we have unread notifications
        unread_count = DiscussionNotification.objects.filter(
            user=team_member,
            is_read=False
        ).count()
        assert unread_count >= 2  # At least 2 notifications (one for each discussion)
        
        # Mark all as read
        url = reverse('project:user-discussion-notifications-mark-all-read')
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify all notifications are marked as read
        unread_count = DiscussionNotification.objects.filter(
            user=team_member,
            is_read=False
        ).count()
        assert unread_count == 0 