from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Apps.documents'
    verbose_name = 'Document Management'

    def ready(self):
        import Apps.documents.signals  # noqa
