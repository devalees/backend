from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'entity'

router = DefaultRouter()
router.register(r'organizations', views.OrganizationViewSet, basename='organization')
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'teams', views.TeamViewSet, basename='team')
router.register(r'team-members', views.TeamMemberViewSet, basename='team_members')
router.register(r'organization-settings', views.OrganizationSettingsViewSet)

urlpatterns = router.urls 