from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContactViewSet, ContactGroupViewSet

router = DefaultRouter()
router.register(r'', ContactViewSet)
router.register(r'groups', ContactGroupViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 