from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Check if 2FA is enabled for admin user'

    def handle(self, *args, **options):
        try:
            admin_user = User.objects.get(username='admin')
            self.stdout.write(f"Admin user found: {admin_user.username}")
            self.stdout.write(f"2FA Enabled: {admin_user.two_factor_enabled}")
            if admin_user.two_factor_enabled:
                self.stdout.write(self.style.SUCCESS('2FA is enabled for admin user'))
            else:
                self.stdout.write(self.style.WARNING('2FA is NOT enabled for admin user'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Admin user not found')) 