from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from Apps.project.models import Project, Task

User = get_user_model()

class Command(BaseCommand):
    help = 'Grants project-related permissions to superuser'

    def handle(self, *args, **options):
        # Get all superusers
        superusers = User.objects.filter(is_superuser=True)
        
        # Get content types
        project_ct = ContentType.objects.get_for_model(Project)
        task_ct = ContentType.objects.get_for_model(Task)
        
        # Get permissions
        project_permissions = Permission.objects.filter(
            content_type=project_ct,
            codename__in=['view_all_projects', 'manage_project_members']
        )
        task_permissions = Permission.objects.filter(
            content_type=task_ct,
            codename__in=['view_all_tasks', 'manage_task_assignments']
        )
        
        for superuser in superusers:
            # Grant project permissions
            superuser.user_permissions.add(*project_permissions)
            
            # Grant task permissions
            superuser.user_permissions.add(*task_permissions)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully granted project permissions to superuser {superuser.username}'
                )
            ) 