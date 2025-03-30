from django.apps import AppConfig


class DataImportExportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Apps.data_import_export'
    verbose_name = 'Data Import Export'

    def ready(self):
        """
        Initialize app when it's ready.
        Import signals here to avoid circular imports.
        """
        import Apps.data_import_export.signals  # noqa
