from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DocumentViewSet, 
    DocumentVersionViewSet, 
    DocumentClassificationViewSet, 
    DocumentTagViewSet
)

app_name = 'documents'

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'versions', DocumentVersionViewSet, basename='document-version')
router.register(r'classifications', DocumentClassificationViewSet, basename='document-classification')
router.register(r'tags', DocumentTagViewSet, basename='document-tag')

urlpatterns = [
    path('', include(router.urls)),
] 