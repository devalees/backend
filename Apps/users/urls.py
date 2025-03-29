from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register(r'', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserViewSet.as_view({'post': 'register'}), name='register'),
    path('password-reset/', UserViewSet.as_view({'post': 'password_reset'}), name='password-reset'),
    path('password-reset-confirm/', UserViewSet.as_view({'post': 'password_reset_confirm'}), name='password-reset-confirm'),
] 