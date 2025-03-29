from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DataTransferViewSet, DataTransferItemViewSet

router = DefaultRouter()
router.register(r'', DataTransferViewSet)
router.register(r'items', DataTransferItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 