from django.apps import AppConfig

class CoreConfig(AppConfig):
    name = 'Apps.core'
    verbose_name = 'Core'
    label = 'core'

    def ready(self):
        try:
            import Apps.core.models  # noqa
        except ImportError:
            pass 