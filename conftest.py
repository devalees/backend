"""
Test configuration file for pytest.
"""

import os
import sys
import django
from django.conf import settings

# Add the project root directory to the Python path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'Apps'))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings_test')

# Initialize Django
django.setup() 