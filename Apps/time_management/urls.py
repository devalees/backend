from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TimeCategoryViewSet, TimeEntryViewSet, TimesheetViewSet,
    TimesheetEntryViewSet, WorkScheduleViewSet
)

router = DefaultRouter()
router.register(r'categories', TimeCategoryViewSet, basename='time-category')
router.register(r'entries', TimeEntryViewSet, basename='time-entry')
router.register(r'timesheets', TimesheetViewSet, basename='timesheet')
router.register(r'timesheet-entries', TimesheetEntryViewSet, basename='timesheet-entry')
router.register(r'schedules', WorkScheduleViewSet, basename='work-schedule')

urlpatterns = [
    path('', include(router.urls)),
] 