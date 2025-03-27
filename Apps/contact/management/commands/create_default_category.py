from django.core.management.base import BaseCommand
from contact.models import ContactCategory

class Command(BaseCommand):
    help = 'Creates the default contact category'

    def handle(self, *args, **kwargs):
        default_category, created = ContactCategory.objects.get_or_create(
            name='Default',
            defaults={
                'description': 'Default category for contacts',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created default category'))
        else:
            self.stdout.write(self.style.SUCCESS('Default category already exists')) 