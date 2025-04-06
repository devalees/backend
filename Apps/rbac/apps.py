from django.apps import AppConfig


class RbacConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Apps.rbac'
    verbose_name = 'Role-Based Access Control'
