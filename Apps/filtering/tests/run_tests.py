#!/usr/bin/env python3
"""
Simple script to run the model validation tests without requiring pytest.
This uses Django's built-in test runner.
"""
import os
import sys
import django
from django.conf import settings
from django.test.runner import DiscoverRunner

# Set up Django environment
if not settings.configured:
    settings.configure(
        DEBUG=True,
        USE_TZ=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sites",
            "Apps.filtering",
        ],
        MIDDLEWARE=[],
        ROOT_URLCONF="",
        SITE_ID=1,
        SECRET_KEY="test_secret_key",
    )
    django.setup()

def run_tests():
    # Use Django's test runner to discover and run tests
    test_runner = DiscoverRunner(verbosity=2, interactive=True)
    failures = test_runner.run_tests(["Apps.filtering.tests.test_model_validation"])
    return failures

if __name__ == "__main__":
    # Add the parent directory to sys.path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
    
    # Run the tests
    failures = run_tests()
    
    # Exit with appropriate status code
    sys.exit(bool(failures)) 