from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExampleModelViewSet

router = DefaultRouter()
router.register(r'examples', ExampleModelViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 