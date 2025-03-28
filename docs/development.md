# Development Guide

## Development Environment Setup

### 1. Global Dependencies Installation
These dependencies should be installed globally on your system:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
sudo apt install postgresql postgresql-contrib redis-server
sudo apt install git

# macOS
brew install python@3.12 postgresql redis git

# Windows
# Download and install:
# - Python 3.12 from python.org
# - PostgreSQL from postgresql.org
# - Redis from redis.io
# - Git from git-scm.com
```

### 2. Project Setup
```bash
# Clone repository
git clone https://github.com/devalees/backend.git
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows

# Install project dependencies in virtual environment
pip install -r requirements.txt
```

### 3. Project Dependencies
The following dependencies are managed through requirements.txt and should be installed in the virtual environment:

#### Core Dependencies
- Django 5.1.7+ - Web framework
- Django REST Framework 3.14.0+ - API framework
- Django Filter 23.5+ - Dynamic filtering
- Django CORS Headers 4.3.1+ - CORS support
- Django Allauth 0.61.1+ - Authentication
- Django Environ 0.11.2+ - Environment variables
- Django Extensions 3.2.3+ - Development tools
- Django Debug Toolbar 4.3.0+ - Debugging
- Django Redis 5.4.0+ - Redis integration
- Django Storages 1.14.2+ - File storage
- Django Celery Beat 2.5.0+ - Task scheduling
- Django Celery Results 2.5.1+ - Task results
- Django Import Export 3.3.7+ - Data import/export

#### Task Queue & Cache
- Celery 5.3.6+ - Task queue
- Redis 5.0.1+ - Cache & message broker

#### Database
- psycopg2-binary 2.9.9+ - PostgreSQL adapter

#### Image Processing
- Pillow 10.2.0+ - Image processing

#### Environment & Deployment
- python-dotenv 1.0.1+ - Environment variables
- gunicorn 21.2.0+ - Production server
- whitenoise 6.6.0+ - Static files

#### Authentication & Security
- pyotp 2.9.0+ - Two-factor authentication
- qrcode 8.0+ - QR code generation

#### Testing & Coverage
- pytest 8.3.5+ - Testing framework
- pytest-django 4.10.0+ - Django test integration
- pytest-cov 6.0.0+ - Coverage reporting
- coverage 7.7.1+ - Code coverage

#### Data Processing
- openpyxl 3.1.5+ - Excel file support
- tablib[xlsx] 3.8.0+ - Data import/export

### 4. Environment Configuration
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