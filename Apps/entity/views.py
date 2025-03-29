from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Organization, Department, Team, TeamMember
from .serializers import OrganizationSerializer, DepartmentSerializer, TeamSerializer, TeamMemberSerializer

# Create your views here.

class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet for Organization model"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def department(self, request, pk=None):
        """Get all departments for an organization"""
        organization = self.get_object()
        departments = organization.departments.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def team_member(self, request, pk=None):
        """Get all team members for an organization"""
        organization = self.get_object()
        team_members = TeamMember.objects.filter(team__department__organization=organization)
        serializer = TeamMemberSerializer(team_members, many=True)
        return Response(serializer.data)

class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Department model"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter departments by organization"""
        organization_id = self.request.query_params.get('organization', None)
        parent_id = self.request.query_params.get('parent', None)
        queryset = Department.objects.all()

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)

        return queryset

    @action(detail=True, methods=['get'])
    def team(self, request, pk=None):
        """Get all teams for a department"""
        department = self.get_object()
        teams = department.teams.all()
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def team_member(self, request, pk=None):
        """Get all team members for a department"""
        department = self.get_object()
        team_members = TeamMember.objects.filter(team__department=department)
        serializer = TeamMemberSerializer(team_members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def child_department(self, request, pk=None):
        """Get all child departments"""
        department = self.get_object()
        child_departments = department.children.all()
        serializer = DepartmentSerializer(child_departments, many=True)
        return Response(serializer.data)

class TeamViewSet(viewsets.ModelViewSet):
    """ViewSet for Team model"""
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter teams by department"""
        department_id = self.request.query_params.get('department', None)
        organization_id = self.request.query_params.get('organization', None)
        queryset = Team.objects.all()

        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if organization_id:
            queryset = queryset.filter(department__organization_id=organization_id)

        return queryset

    @action(detail=True, methods=['get'])
    def team_member(self, request, pk=None):
        """Get all members for a team"""
        team = self.get_object()
        members = team.members.all()
        serializer = TeamMemberSerializer(members, many=True)
        return Response(serializer.data)

class TeamMemberViewSet(viewsets.ModelViewSet):
    """ViewSet for TeamMember model"""
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter team members by team, department, or organization"""
        team_id = self.request.query_params.get('team', None)
        department_id = self.request.query_params.get('department', None)
        organization_id = self.request.query_params.get('organization', None)
        queryset = TeamMember.objects.all()

        if team_id:
            queryset = queryset.filter(team_id=team_id)
        if department_id:
            queryset = queryset.filter(team__department_id=department_id)
        if organization_id:
            queryset = queryset.filter(team__department__organization_id=organization_id)

        return queryset
