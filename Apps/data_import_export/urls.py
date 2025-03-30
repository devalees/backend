from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ImportExportConfigViewSet, ImportExportLogViewSet

app_name = 'data_import_export'

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'configs', ImportExportConfigViewSet, basename='importexportconfig')
router.register(r'logs', ImportExportLogViewSet, basename='importexportlog')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]
