import pytest
import time
import ssl
from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError

def test_elasticsearch_connection():
    """Test that Elasticsearch connection can be established"""
    try:
        # Create a custom SSL context for testing
        ssl_context = ssl.create_default_context()
        # For testing purposes, we'll still use verify_certs=False but with a proper SSL context
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Create Elasticsearch client with settings
        es = Elasticsearch(
            settings.ELASTICSEARCH_DSN,
            basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD),
            verify_certs=settings.ELASTICSEARCH_VERIFY_CERTS,
            ssl_context=ssl_context
        )
        
        # Test connection
        assert es.ping() is True
        
        # Test basic index operations
        test_index = f"{settings.ELASTICSEARCH_INDEX_PREFIX}test"
        
        # Create index if it doesn't exist
        if not es.indices.exists(index=test_index):
            es.indices.create(index=test_index)
        
        test_doc = {
            'title': 'Test Document',
            'content': 'This is a test document'
        }
        
        # Create test document
        response = es.index(index=test_index, document=test_doc)
        assert response['result'] in ['created', 'updated']
        
        # Add a small delay to ensure the document is indexed
        time.sleep(1)
        
        # Search for test document
        search_response = es.search(index=test_index, query={'match': {'title': 'Test Document'}})
        print(f"Search response: {search_response}")
        print(f"Total hits: {search_response['hits']['total']['value']}")
        
        # Refresh the index to ensure the document is searchable
        es.indices.refresh(index=test_index)
        
        # Search again after refreshing
        search_response = es.search(index=test_index, query={'match': {'title': 'Test Document'}})
        print(f"Search response after refresh: {search_response}")
        print(f"Total hits after refresh: {search_response['hits']['total']['value']}")
        
        assert search_response['hits']['total']['value'] > 0
        
        # Clean up test index
        es.indices.delete(index=test_index, ignore=[400, 404])
        
    except ConnectionError as e:
        pytest.fail(f"Failed to connect to Elasticsearch: {str(e)}")
    except Exception as e:
        pytest.fail(f"Elasticsearch test failed: {str(e)}") 