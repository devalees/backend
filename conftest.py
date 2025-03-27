import os
import sys
import pytest

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass 