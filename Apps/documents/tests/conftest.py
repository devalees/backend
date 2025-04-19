# This file is intentionally left empty.
# It's used by pytest to automatically discover tests in this directory. 

import pytest
from elasticsearch import Elasticsearch
from django.conf import settings

@pytest.fixture(scope="session")
def es_client():
    """
    Create an Elasticsearch client for testing that uses HTTP instead of HTTPS.
    This fixture will be available for all test functions in the documents app.
    """
    # Create a client using HTTP instead of HTTPS to avoid SSL issues during tests
    es = Elasticsearch(
        ['http://localhost:9201'],
        verify_certs=False,
        basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD) if hasattr(settings, 'ELASTICSEARCH_USERNAME') else None
    )
    
    # Create test index if it doesn't exist
    test_index = f"{settings.ELASTICSEARCH_INDEX_PREFIX}test"
    if not es.indices.exists(index=test_index):
        es.indices.create(
            index=test_index,
            mappings={
                "properties": {
                    "title": {"type": "text"},
                    "content": {"type": "text"},
                    "tags": {"type": "keyword"}
                }
            }
        )
    
    yield es
    
    # Clean up test index
    if es.indices.exists(index=test_index):
        es.indices.delete(index=test_index) 