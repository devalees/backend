from django.apps import AppConfig


class ContactsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Apps.contacts'
    verbose_name = 'Contacts'
    label = 'contacts'

    def ready(self):
        """
        Initialize app and register signals
        """
        try:
            import Apps.contacts.models  # noqa
        except ImportError:
            pass
