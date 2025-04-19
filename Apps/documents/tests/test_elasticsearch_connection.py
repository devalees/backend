"""
Tests for Elasticsearch connection and functionality.
"""
import pytest
from elasticsearch import Elasticsearch
from django.conf import settings
import logging
import ssl

logger = logging.getLogger(__name__)

@pytest.fixture
def es_client():
    """
    Create an Elasticsearch client for testing.
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

def test_elasticsearch_connection():
    """
    Test basic Elasticsearch connection.
    """
    try:
        # Create client using HTTP instead of HTTPS
        es = Elasticsearch(
            ['http://localhost:9201'],
            verify_certs=False,
            basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD) if hasattr(settings, 'ELASTICSEARCH_USERNAME') else None
        )
        
        # Verify connection
        assert es.ping() is True
        
        # Test basic operations
        test_index = f"{settings.ELASTICSEARCH_INDEX_PREFIX}connection_test"
        
        # Create test index
        if es.indices.exists(index=test_index):
            es.indices.delete(index=test_index)
            
        es.indices.create(
            index=test_index,
            mappings={
                "properties": {
                    "title": {"type": "text"},
                    "content": {"type": "text"}
                }
            }
        )
        
        # Add test document
        doc = {
            "title": "Test Document",
            "content": "This is a test document for Elasticsearch connection"
        }
        
        resp = es.index(index=test_index, document=doc)
        assert resp['result'] == 'created'
        
        # Refresh index
        es.indices.refresh(index=test_index)
        
        # Search
        query = {
            "query": {
                "match": {
                    "title": "Test"
                }
            }
        }
        
        search_resp = es.search(index=test_index, body=query)
        assert search_resp['hits']['total']['value'] > 0
        
        # Clean up
        es.indices.delete(index=test_index)
        
    except Exception as e:
        pytest.fail(f"Elasticsearch test failed: {str(e)}") 