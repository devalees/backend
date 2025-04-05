from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from ..models import Organization, Department, Team, TeamMember
from ..factories import OrganizationFactory, DepartmentFactory, TeamFactory, TeamMemberFactory, UserFactory
from django.contrib.auth import get_user_model

User = get_user_model()

class TestOrganizationAnalytics(APITestCase):
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.organization = OrganizationFactory()
        self.user = UserFactory()
        
        # Create a department
        self.department = DepartmentFactory(
            organization=self.organization,
            name="Test Department"
        )
        
        # Create a team in the department
        self.team = TeamFactory(
            department=self.department,
            name="Test Team"
        )
        
        # Add the user as a team member
        self.team_member = TeamMemberFactory(
            team=self.team,
            user=self.user
        )
        
        # Authenticate the user
        self.client.force_authenticate(user=self.user)

    def test_get_organization_stats(self):
        """Test retrieving organization statistics"""
        # Create additional test data with unique names
        teams = [
            TeamFactory(
                department=DepartmentFactory(
                    organization=self.organization,
                    name=f"Department {i}"
                ),
                name=f"Team {i}"
            ) for i in range(3)
        ]
        
        members = [
            TeamMemberFactory(
                team=teams[i % len(teams)],
                user=UserFactory()
            ) for i in range(5)
        ]

        url = reverse('entity:organization-analytics', kwargs={'pk': self.organization.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_teams'], 4)  # 3 new teams + 1 from setUp
        self.assertEqual(response.data['total_departments'], 4)  # 3 new departments + 1 from setUp
        self.assertEqual(response.data['total_members'], 6)  # 5 new members + 1 from setUp

    def test_get_organization_activity(self):
        """Test retrieving organization activity metrics"""
        url = reverse('entity:organization-activity', kwargs={'pk': self.organization.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recent_activities', response.data)
        self.assertIn('engagement_metrics', response.data)

    def test_get_organization_performance(self):
        """Test retrieving organization performance metrics"""
        url = reverse('entity:organization-performance', kwargs={'pk': self.organization.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('team_performance', response.data)
        self.assertIn('department_performance', response.data)
        self.assertIn('member_contributions', response.data)

    def test_get_organization_growth(self):
        """Test retrieving organization growth metrics"""
        url = reverse('entity:organization-growth', kwargs={'pk': self.organization.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('member_growth', response.data)
        self.assertIn('team_growth', response.data)
        self.assertIn('department_growth', response.data)

    def test_unauthorized_access(self):
        """Test unauthorized access to analytics"""
        unauthorized_user = UserFactory()
        self.client.force_authenticate(user=unauthorized_user)

        urls = [
            reverse('entity:organization-analytics', kwargs={'pk': self.organization.pk}),
            reverse('entity:organization-activity', kwargs={'pk': self.organization.pk}),
            reverse('entity:organization-performance', kwargs={'pk': self.organization.pk}),
            reverse('entity:organization-growth', kwargs={'pk': self.organization.pk})
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 