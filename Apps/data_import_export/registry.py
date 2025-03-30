from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from .models import ImportExportConfig

def register_all_models():
    """Register all models for import/export functionality"""
    # List of all models to register
    models_to_register = [
        # Project Management
        'project.Project',
        'project.Task',
        'project.ProjectTemplate',
        'project.TaskTemplate',
        
        # Entity Management
        'entity.Organization',
        'entity.Department',
        'entity.Team',
        
        # Time Management
        'time_management.TimeCategory',
        'time_management.TimeEntry',
        'time_management.Timesheet',
        'time_management.WorkSchedule',
        
        # RBAC
        'rbac.Role',
        'rbac.Permission',
        'rbac.FieldPermission',
        'rbac.RolePermission',
        
        # Contacts
        'contacts.Contact',
        
        # Users
        'users.User',
    ]
    
    for model_path in models_to_register:
        try:
            app_label, model_name = model_path.split('.')
            model = apps.get_model(app_label, model_name)
            content_type = ContentType.objects.get_for_model(model)
            
            # Create default configuration if it doesn't exist
            config, created = ImportExportConfig.objects.get_or_create(
                content_type=content_type,
                name=f"Default {model_name} Import/Export",
                defaults={
                    'description': f"Default import/export configuration for {model_name}",
                    'field_mapping': {
                        field.name: field.name 
                        for field in model._meta.fields 
                        if field.name not in ['id', 'created_at', 'updated_at']
                    }
                }
            )
            
            if created:
                print(f"Created import/export config for {model_path}")
            else:
                print(f"Import/export config already exists for {model_path}")
                
        except Exception as e:
            print(f"Error registering {model_path}: {str(e)}") 