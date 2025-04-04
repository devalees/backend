from django.apps import AppConfig


class AutomationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Apps.automation'
    label = 'automation'
    verbose_name = 'Workflow Automation'

    def ready(self):
        """
        Initialize app and register signals
        """
        try:
            import Apps.automation.signals  # noqa
        except ImportError:
            pass 