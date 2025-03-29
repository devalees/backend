"""
Test configuration file for pytest.
"""

import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings')
django.setup() 