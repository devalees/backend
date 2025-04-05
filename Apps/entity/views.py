from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Organization, Department, Team, TeamMember, OrganizationSettings
from .serializers import (
    OrganizationSerializer, DepartmentSerializer, 
    TeamSerializer, TeamMemberSerializer,
    OrganizationSettingsSerializer
)
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .permissions import IsOrganizationMember

# Create your views here.

class OrganizationViewSet(viewsets.ModelViewSet):
    """ViewSet for Organization model"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsOrganizationMember]

    def get_queryset(self):
        return Organization.objects.filter(
            Q(departments__teams__members__user=self.request.user)
        ).distinct()

    def get_object(self):
        # Get the object from the queryset first
        obj = Organization.objects.get(pk=self.kwargs['pk'])
        # Check object permissions
        self.check_object_permissions(self.request, obj)
        return obj

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
        team_members = TeamMember.all_objects.filter(team__department__organization=organization)
        serializer = TeamMemberSerializer(team_members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        try:
            organization = self.get_object()
            
            # Get total counts
            total_departments = organization.departments.count()
            total_teams = Team.objects.filter(department__organization=organization).count()
            total_members = TeamMember.objects.filter(team__department__organization=organization).count()
            
            return Response({
                'total_departments': total_departments,
                'total_teams': total_teams,
                'total_members': total_members
            })
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def activity(self, request, pk=None):
        try:
            organization = self.get_object()
            
            # Get recent activity metrics
            now = timezone.now()
            last_week = now - timedelta(days=7)
            
            recent_activities = TeamMember.objects.filter(
                team__department__organization=organization,
                created_at__gte=last_week
            ).count()
            
            # Calculate engagement metrics
            total_members = TeamMember.objects.filter(
                team__department__organization=organization
            ).count()
            
            engagement_metrics = {
                'active_members': recent_activities,
                'total_members': total_members,
                'engagement_rate': round(recent_activities / total_members * 100 if total_members > 0 else 0, 2)
            }
            
            return Response({
                'recent_activities': recent_activities,
                'engagement_metrics': engagement_metrics
            })
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        try:
            organization = self.get_object()
            
            # Get team performance metrics
            team_performance = Team.objects.filter(
                department__organization=organization
            ).annotate(
                member_count=Count('members')
            ).values('name', 'member_count')
            
            # Get department performance metrics
            department_performance = Department.objects.filter(
                organization=organization
            ).annotate(
                team_count=Count('teams'),
                member_count=Count('teams__members')
            ).values('name', 'team_count', 'member_count')
            
            # Get member contributions
            member_contributions = TeamMember.objects.filter(
                team__department__organization=organization
            ).values('user__username').annotate(
                teams_count=Count('team', distinct=True)
            )
            
            return Response({
                'team_performance': team_performance,
                'department_performance': department_performance,
                'member_contributions': member_contributions
            })
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def growth(self, request, pk=None):
        try:
            organization = self.get_object()
            
            # Calculate growth metrics
            now = timezone.now()
            last_month = now - timedelta(days=30)
            
            # Member growth
            member_growth = {
                'new_members': TeamMember.objects.filter(
                    team__department__organization=organization,
                    created_at__gte=last_month
                ).count(),
                'total_members': TeamMember.objects.filter(
                    team__department__organization=organization
                ).count()
            }
            
            # Team growth
            team_growth = {
                'new_teams': Team.objects.filter(
                    department__organization=organization,
                    created_at__gte=last_month
                ).count(),
                'total_teams': Team.objects.filter(
                    department__organization=organization
                ).count()
            }
            
            # Department growth
            department_growth = {
                'new_departments': Department.objects.filter(
                    organization=organization,
                    created_at__gte=last_month
                ).count(),
                'total_departments': Department.objects.filter(
                    organization=organization
                ).count()
            }
            
            return Response({
                'member_growth': member_growth,
                'team_growth': team_growth,
                'department_growth': department_growth
            })
        except Organization.DoesNotExist:
            return Response(
                {'error': 'Organization not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Department model"""
    queryset = Department.all_objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter departments by organization"""
        organization_id = self.request.query_params.get('organization', None)
        parent_id = self.request.query_params.get('parent', None)
        queryset = Department.all_objects.all()

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
        team_members = TeamMember.all_objects.filter(team__department=department)
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
    queryset = Team.all_objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter teams by department"""
        department_id = self.request.query_params.get('department', None)
        organization_id = self.request.query_params.get('organization', None)
        queryset = Team.all_objects.all()

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
    queryset = TeamMember.all_objects.all()
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter team members by team, department, or organization"""
        team_id = self.request.query_params.get('team', None)
        department_id = self.request.query_params.get('department', None)
        organization_id = self.request.query_params.get('organization', None)
        queryset = TeamMember.all_objects.all()

        if team_id:
            queryset = queryset.filter(team_id=team_id)
        if department_id:
            queryset = queryset.filter(team__department_id=department_id)
        if organization_id:
            queryset = queryset.filter(team__department__organization_id=organization_id)

        return queryset

class OrganizationSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for OrganizationSettings model"""
    queryset = OrganizationSettings.objects.all()
    serializer_class = OrganizationSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter settings by organization"""
        organization_id = self.request.query_params.get('organization', None)
        queryset = OrganizationSettings.objects.all()

        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        return queryset

    @action(detail=False, methods=['get'])
    def get_by_organization(self, request):
        """Get settings for a specific organization"""
        organization_id = request.query_params.get('organization')
        if not organization_id:
            return Response(
                {"error": "Organization ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            settings = OrganizationSettings.objects.get(organization_id=organization_id)
            serializer = self.get_serializer(settings)
            return Response(serializer.data)
        except OrganizationSettings.DoesNotExist:
            return Response(
                {"error": "Settings not found for this organization"},
                status=status.HTTP_404_NOT_FOUND
            )

    def create(self, request, *args, **kwargs):
        """Create organization settings"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        """Update organization settings"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            self.perform_update(serializer)
            return Response(serializer.data)
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
