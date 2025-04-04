from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NodeViewSet,
    ConnectionViewSet,
    WorkflowTemplateViewSet,
    WorkflowViewSet,
    ReportTemplateViewSet,
    ReportViewSet,
    ReportScheduleViewSet
)

app_name = 'automation'

router = DefaultRouter()

# Register viewsets with explicit basenames to match test expectations
router.register(r'nodes', NodeViewSet, basename='node')
router.register(r'connections', ConnectionViewSet, basename='connection')
router.register(r'workflow-templates', WorkflowTemplateViewSet, basename='workflowtemplate')
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'report-templates', ReportTemplateViewSet, basename='reporttemplate')
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'report-schedules', ReportScheduleViewSet, basename='reportschedule')

# The router will automatically generate URLs for custom actions:
# - PATCH /api/v1/automation/nodes/{pk}/position/ -> node-position
# - POST /api/v1/automation/workflow-templates/{pk}/instantiate/ -> workflowtemplate-instantiate
# - POST /api/v1/automation/workflows/{pk}/validate/ -> workflow-validate

urlpatterns = [
    path('', include(router.urls)),
]