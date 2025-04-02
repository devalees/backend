"""
RBAC app configuration.
"""

from django.apps import AppConfig

class RbacConfig(AppConfig):
    """
    AppConfig for RBAC.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Apps.rbac'
    verbose_name = 'Role-Based Access Control'

    def ready(self):
        """
        Import signals when app is ready.
        """
        import Apps.rbac.signals  # noqa 