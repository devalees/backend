from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactViewSet, ContactGroupViewSet, ContactTemplateViewSet, CommunicationViewSet, CommunicationTemplateViewSet, CommunicationMonitoringViewSet

router = DefaultRouter()
router.register(r'', ContactViewSet)
router.register(r'groups', ContactGroupViewSet)
router.register(r'templates', ContactTemplateViewSet)
router.register(r'communications', CommunicationViewSet)
router.register(r'communication-templates', CommunicationTemplateViewSet)
router.register(r'communication-activities', CommunicationMonitoringViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 