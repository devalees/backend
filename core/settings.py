# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'entity.apps.EntityConfig',
    'users.apps.UsersConfig',
    'contact.apps.ContactConfig',
    'Apps.field_control.apps.FieldControlConfig',  # Updated path to use Apps directory
]

# ... existing code ... 