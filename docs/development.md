# Development Guide

## Development Environment Setup

### 1. Prerequisites Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
sudo apt install postgresql postgresql-contrib redis-server

# macOS
brew install python@3.12 postgresql redis

# Windows
# Download Python 3.12 from python.org
# Download PostgreSQL from postgresql.org
# Download Redis from redis.io
```

### 2. Project Setup
```bash
# Clone repository
git clone https://github.com/devalees/Project-Management.git
cd Project-Management

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Set up pre-commit hooks
pre-commit install
```

### 3. Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
DEBUG=True
```

## Development Workflow

### 1. Git Workflow
```bash
# Create feature branch
git checkout -b feature/feature-name

# Make changes and commit
git add .
git commit -m "feat: add feature description"

# Push changes
git push origin feature/feature-name

# Create pull request on GitHub
```

### 2. Code Style Guide

#### Python Style
- Follow PEP 8
- Use Black for formatting
- Maximum line length: 88 characters
- Use type hints

```python
from typing import List, Optional

def get_active_users(organization_id: int) -> List[User]:
    """
    Get all active users in an organization.
    
    Args:
        organization_id: The ID of the organization
        
    Returns:
        List of active User objects
    """
    return User.objects.filter(
        organization_id=organization_id,
        is_active=True
    )
```

#### Django Best Practices
```python
# models.py
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Organization(TimeStampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
```

### 3. Testing Guidelines

#### Writing Tests
```python
# test_models.py
from django.test import TestCase
from django.core.exceptions import ValidationError

class OrganizationModelTest(TestCase):
    def setUp(self):
        self.org_data = {
            'name': 'Test Org',
            'description': 'Test Description'
        }

    def test_organization_creation(self):
        org = Organization.objects.create(**self.org_data)
        self.assertEqual(org.name, self.org_data['name'])
```

#### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific test file
python manage.py test apps.entity.tests.test_models

# Run with coverage
coverage run manage.py test
coverage report
coverage html  # Generate HTML report
```

### 4. Database Management

#### Migrations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Revert migration
python manage.py migrate app_name migration_name
```

#### Database Backup/Restore
```bash
# Backup
python manage.py dumpdata > backup.json

# Restore
python manage.py loaddata backup.json
```

### 5. Development Server

#### Running the Server
```bash
# Start development server
python manage.py runserver

# Start with specific port
python manage.py runserver 8080

# Start Celery worker
celery -A core worker -l info

# Start Celery beat
celery -A core beat -l info
```

#### Development Tools
```bash
# Django shell
python manage.py shell_plus

# Database shell
python manage.py dbshell

# Clear cache
python manage.py clear_cache
```

## Debugging

### 1. Django Debug Toolbar
- Installed in development environment
- Shows SQL queries, templates, cache operations
- Access at /__debug__/ when DEBUG=True

### 2. Logging Configuration
```python
# settings/development.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}
```

### 3. Using pdb
```python
def complex_function():
    x = calculate_something()
    import pdb; pdb.set_trace()  # Debugger will stop here
    y = another_calculation(x)
```

## Performance Optimization

### 1. Database Optimization
```python
# Use select_related for ForeignKey
users = User.objects.select_related('profile').all()

# Use prefetch_related for ManyToMany
orgs = Organization.objects.prefetch_related('members').all()

# Bulk operations
Organization.objects.bulk_create([
    Organization(name=f"Org {i}") for i in range(100)
])
```

### 2. Caching
```python
# View caching
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def organization_list(request):
    return Organization.objects.all()

# Template fragment caching
{% load cache %}
{% cache 500 sidebar request.user.username %}
    ... expensive template ...
{% endcache %}
```

## Security Considerations

### 1. Security Headers
```python
# settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
```

### 2. Password Validation
```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

## Troubleshooting

### Common Issues

1. **Migration Conflicts**
```bash
# Reset migrations
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
python manage.py makemigrations
```

2. **Static Files Not Found**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
```

3. **Database Connection Issues**
```bash
# Check database settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

## Additional Resources

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.org/)

### Tools
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
- [Django Extensions](https://django-extensions.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/) 