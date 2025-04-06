from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserRoleViewSet

app_name = 'rbac'  # Add app_name for namespace

router = DefaultRouter()
router.register(r'user-roles', UserRoleViewSet, basename='userrole')

urlpatterns = [
    path('', include(router.urls)),
] 