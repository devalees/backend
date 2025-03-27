from django.urls import path
from . import views

urlpatterns = [
    path('2fa/', views.two_factor_page, name='2fa_page'),
    path('2fa/setup/', views.setup_2fa, name='setup_2fa'),
    path('2fa/verify/', views.verify_2fa, name='verify_2fa'),
    path('2fa/disable/', views.disable_2fa, name='disable_2fa'),
    path('2fa/backup-codes/', views.generate_backup_codes, name='generate_backup_codes'),
] 