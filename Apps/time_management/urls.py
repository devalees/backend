from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TimeCategoryViewSet, TimeEntryViewSet, TimesheetViewSet,
    TimesheetEntryViewSet, WorkScheduleViewSet
)

# Define the app name for namespacing
app_name = 'time-management'

router = DefaultRouter()
router.register(r'categories', TimeCategoryViewSet, basename='time-category')
router.register(r'entries', TimeEntryViewSet, basename='time-entry')
router.register(r'timesheets', TimesheetViewSet, basename='timesheet')
router.register(r'timesheet-entries', TimesheetEntryViewSet, basename='timesheet-entry')
router.register(r'schedules', WorkScheduleViewSet, basename='work-schedule')

# Explicit paths for timesheet actions to ensure they are accessible
timesheet_actions = [
    path('timesheets/<int:pk>/approve/', TimesheetViewSet.as_view({'post': 'approve'}), name='timesheet-approve'),
    path('timesheets/<int:pk>/reject/', TimesheetViewSet.as_view({'post': 'reject'}), name='timesheet-reject'),
]

urlpatterns = [
    path('', include(router.urls)),
] + timesheet_actions 