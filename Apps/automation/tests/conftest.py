"""
Pytest configuration file for automation tests.
"""
import pytest

def pytest_configure(config):
    """Register custom marks."""
    config.addinivalue_line(
        "markers",
        "celery: mark test to run with celery configuration"
    ) 