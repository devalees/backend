from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactViewSet, ContactGroupViewSet, ContactTemplateViewSet

router = DefaultRouter()
router.register(r'', ContactViewSet)
router.register(r'groups', ContactGroupViewSet)
router.register(r'templates', ContactTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 