from django.core.management.base import BaseCommand
from Apps.data_import_export.registry import register_all_models

class Command(BaseCommand):
    help = 'Register all models for import/export functionality'

    def handle(self, *args, **options):
        self.stdout.write('Starting model registration for import/export...')
        register_all_models()
        self.stdout.write(self.style.SUCCESS('Successfully registered all models for import/export')) 