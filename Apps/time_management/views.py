from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum
from .models import TimeCategory, TimeEntry, Timesheet, TimesheetEntry, WorkSchedule
from .serializers import (
    TimeCategorySerializer, TimeEntrySerializer, TimesheetSerializer,
    TimesheetEntrySerializer, WorkScheduleSerializer
)

# Create your views here.

class TimeCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing time categories.
    Supports CRUD operations with appropriate permissions.
    """
    queryset = TimeCategory.objects.all()
    serializer_class = TimeCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class TimeEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing time entries.
    Supports CRUD operations and filtering by date range and project.
    """
    serializer_class = TimeEntrySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'project__name']
    ordering_fields = ['start_time', 'end_time', 'hours']
    ordering = ['-start_time']

    def get_queryset(self):
        queryset = TimeEntry.objects.filter(user=self.request.user)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        project_id = self.request.query_params.get('project_id', None)

        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__date__lte=end_date)
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, created_by=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of time entries for the current user."""
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        queryset = self.get_queryset()
        if start_date:
            queryset = queryset.filter(start_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__date__lte=end_date)

        total_hours = queryset.aggregate(total=Sum('hours'))['total'] or 0
        billable_hours = queryset.filter(is_billable=True).aggregate(total=Sum('hours'))['total'] or 0
        
        return Response({
            'total_hours': total_hours,
            'billable_hours': billable_hours,
            'non_billable_hours': total_hours - billable_hours
        })

class TimesheetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing timesheets.
    Supports CRUD operations and status transitions.
    """
    serializer_class = TimesheetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['start_date', 'end_date', 'status']
    ordering = ['-start_date']

    def get_queryset(self):
        return Timesheet.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit timesheet for approval."""
        timesheet = self.get_object()
        if timesheet.status != 'draft':
            return Response(
                {'detail': 'Only draft timesheets can be submitted.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        timesheet.status = 'submitted'
        timesheet.submitted_at = timezone.now()
        timesheet.save()
        return Response({'status': 'timesheet submitted'})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a submitted timesheet."""
        timesheet = self.get_object()
        if timesheet.status != 'submitted':
            return Response(
                {'detail': 'Only submitted timesheets can be approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        timesheet.status = 'approved'
        timesheet.approved_at = timezone.now()
        timesheet.approved_by = request.user
        timesheet.save()
        return Response({'status': 'timesheet approved'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a submitted timesheet."""
        timesheet = self.get_object()
        if timesheet.status != 'submitted':
            return Response(
                {'detail': 'Only submitted timesheets can be rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        timesheet.status = 'rejected'
        timesheet.save()
        return Response({'status': 'timesheet rejected'})

class TimesheetEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing timesheet entries.
    Supports CRUD operations with appropriate validations.
    """
    serializer_class = TimesheetEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TimesheetEntry.objects.filter(timesheet__user=self.request.user)

    def perform_create(self, serializer):
        timesheet = serializer.validated_data['timesheet']
        if timesheet.user != self.request.user:
            raise serializers.ValidationError("You can only add entries to your own timesheet.")
        if timesheet.status != 'draft':
            raise serializers.ValidationError("You can only add entries to draft timesheets.")
        serializer.save()

class WorkScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing work schedules.
    Supports CRUD operations and schedule management.
    """
    serializer_class = WorkScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WorkSchedule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get the current active work schedule."""
        schedule = self.get_queryset().filter(is_active=True).first()
        if not schedule:
            return Response(
                {'detail': 'No active work schedule found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(schedule)
        return Response(serializer.data)
