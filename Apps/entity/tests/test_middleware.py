import pytest
from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from Apps.entity.middleware import OrganizationMiddleware
from Apps.entity.models import Organization, Department, Team, TeamMember
from django.test import TestCase
from django.http import HttpResponse
from django.utils import timezone
from Apps.users.models import User
from django.urls import reverse

User = get_user_model()

@pytest.mark.django_db
class TestOrganizationMiddleware:
    @pytest.fixture
    def middleware(self):
        return OrganizationMiddleware(get_response=lambda request: None)

    @pytest.fixture
    def request_factory(self):
        return RequestFactory()

    @pytest.fixture
    def organization(self, user):
        return Organization.objects.create(name="Test Org", created_by=user)

    @pytest.fixture
    def department(self, organization, user):
        return Department.objects.create(name="Test Dept", organization=organization, created_by=user)

    @pytest.fixture
    def team(self, department, user):
        return Team.objects.create(name="Test Team", department=department, created_by=user)

    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_middleware_with_authenticated_user(self, middleware, request_factory, user, team):
        """Test middleware with authenticated user and active team"""
        TeamMember.objects.create(team=team, user=user, created_by=user)
        request = request_factory.get('/')
        request.user = user
        
        response = middleware(request)
        assert response is None
        assert request.organization == team.department.organization
        assert request.department == team.department
        assert request.team == team

    def test_middleware_with_user_no_teams(self, middleware, request_factory, user):
        """Test middleware with authenticated user but no teams"""
        request = request_factory.get('/')
        request.user = user
        
        response = middleware(request)
        assert response is None
        assert request.organization is None
        assert request.department is None
        assert request.team is None

    def test_middleware_with_inactive_team_member(self, middleware, request_factory, user, team):
        """Test middleware with inactive team member"""
        member = TeamMember.objects.create(team=team, user=user, created_by=user)
        member.is_active = False
        member.save()
        
        request = request_factory.get('/')
        request.user = user
        
        response = middleware(request)
        assert response is None
        assert request.organization is None
        assert request.department is None
        assert request.team is None

    def test_middleware_with_inactive_team(self, middleware, request_factory, user, team):
        """Test middleware with inactive team"""
        TeamMember.objects.create(team=team, user=user, created_by=user)
        team.is_active = False
        team.save()
        
        request = request_factory.get('/')
        request.user = user
        
        response = middleware(request)
        assert response is None
        assert request.organization is None
        assert request.department is None
        assert request.team is None

    def test_middleware_with_inactive_department(self, middleware, request_factory, user, team):
        """Test middleware with inactive department"""
        TeamMember.objects.create(team=team, user=user, created_by=user)
        team.department.is_active = False
        team.department.save()
        
        request = request_factory.get('/')
        request.user = user
        
        response = middleware(request)
        assert response is None
        assert request.organization is None
        assert request.department is None
        assert request.team is None

    def test_middleware_with_inactive_organization(self, middleware, request_factory, user, team):
        """Test middleware with inactive organization"""
        TeamMember.objects.create(team=team, user=user, created_by=user)
        team.department.organization.is_active = False
        team.department.organization.save()
        
        request = request_factory.get('/')
        request.user = user
        
        response = middleware(request)
        assert response is None
        assert request.organization is None
        assert request.department is None
        assert request.team is None

    def test_middleware_with_anonymous_user(self, middleware, request_factory):
        """Test middleware with anonymous user"""
        request = request_factory.get('/')
        request.user = None
        
        response = middleware(request)
        assert response is None
        assert request.organization is None
        assert request.department is None
        assert request.team is None

    def test_middleware_with_multiple_teams(self, middleware, request_factory, user, organization):
        """Test middleware with user in multiple teams"""
        dept1 = Department.objects.create(name="Dept 1", organization=organization, created_by=user)
        dept2 = Department.objects.create(name="Dept 2", organization=organization, created_by=user)
        team1 = Team.objects.create(name="Team 1", department=dept1, created_by=user)
        team2 = Team.objects.create(name="Team 2", department=dept2, created_by=user)
        
        TeamMember.objects.create(team=team1, user=user, created_by=user)
        TeamMember.objects.create(team=team2, user=user, created_by=user)
        
        request = request_factory.get('/')
        request.user = user
        
        response = middleware(request)
        assert response is None
        # Should use the first team found
        assert request.organization == organization
        assert request.department == dept1
        assert request.team == team1
