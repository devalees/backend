from django.apps import AppConfig


class ProjectConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Apps.project'
    label = 'project'

    def ready(self):
        import Apps.project.signals  # noqa
