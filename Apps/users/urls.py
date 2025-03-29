from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

app_name = 'users'  # Add app_name for namespace

router = DefaultRouter()
router.register(r'', UserViewSet, basename='users')

# The router will generate URLs like:
# users-list, users-detail, users-password-reset, etc.

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserViewSet.as_view({'post': 'register'}), name='register'),
    path('password-reset/', UserViewSet.as_view({'post': 'password_reset'}), name='password-reset'),
    path('password-reset-confirm/', UserViewSet.as_view({'post': 'password_reset_confirm'}), name='password-reset-confirm'),
    # 2FA endpoints
    path('verify-2fa/', UserViewSet.as_view({'post': 'verify_2fa'}), name='verify-2fa'),
    path('enable-2fa/', UserViewSet.as_view({'post': 'enable_2fa'}), name='enable-2fa'),
    path('confirm-2fa/', UserViewSet.as_view({'post': 'confirm_2fa'}), name='confirm-2fa'),
    path('disable-2fa/', UserViewSet.as_view({'post': 'disable_2fa'}), name='disable-2fa'),
    path('generate-backup-codes/', UserViewSet.as_view({'post': 'generate_backup_codes'}), name='generate-backup-codes'),
    path('verify-backup-code/', UserViewSet.as_view({'post': 'verify_backup_code'}), name='verify-backup-code'),
] 